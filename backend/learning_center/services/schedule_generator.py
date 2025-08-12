# learning_center/services/schedule_generator.py
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from django.db.models import Q, Count
from ..models import *
import logging

logger = logging.getLogger(__name__)

class ScheduleGenerator:
    """
    Умный генератор расписания с учетом всех ограничений бизнеса
    """
    
    def __init__(self):
        self.conflicts = []
    
    def generate_schedule(self, branch_id: int, week_start: datetime) -> Dict:
        """
        Основной алгоритм генерации расписания
        
        Args:
            branch_id: ID филиала
            week_start: Начало недели для планирования
            
        Returns:
            Dict с результатами генерации и конфликтами
        """
        try:
            branch = Branch.objects.get(id=branch_id)
            active_groups = Group.objects.filter(branch=branch, is_active=True)
            
            logger.info(f"Генерация расписания для {branch.name}, неделя {week_start.strftime('%d.%m.%Y')}")
            
            # Этап 1: Анализ доступности ресурсов
            available_slots = self._analyze_resource_availability(branch, week_start)
            
            # Этап 2: Планирование обычных занятий
            regular_lessons = self._schedule_regular_lessons(active_groups, available_slots, week_start)
            
            # Этап 3: Планирование специальных занятий (контрольные + лексика)
            special_lessons = self._schedule_special_lessons(active_groups, available_slots, week_start)
            
            # Этап 4: Распределение компенсационной работы
            compensation_work = self._distribute_compensation_work(active_groups, available_slots, week_start)
            
            # Этап 5: Обнаружение и разрешение конфликтов
            conflicts = self._detect_and_resolve_conflicts(regular_lessons + special_lessons)
            
            # Этап 6: Оптимизация использования пикового времени
            optimized_schedule = self._optimize_peak_time_usage(regular_lessons + special_lessons, branch)
            
            return {
                'status': 'success',
                'regular_lessons': regular_lessons,
                'special_lessons': special_lessons,
                'compensation_work': compensation_work,
                'conflicts': conflicts,
                'optimized_schedule': optimized_schedule,
                'statistics': self._calculate_statistics(regular_lessons, special_lessons, branch)
            }
            
        except Exception as e:
            logger.error(f"Ошибка генерации расписания: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'conflicts': self.conflicts
            }
    
    def _analyze_resource_availability(self, branch: Branch, week_start: datetime) -> Dict:
        """Анализ доступности кабинетов и преподавателей"""
        
        # Доступные кабинеты
        classrooms = list(branch.classrooms.filter(is_active=True))
        
        # Доступные преподаватели
        teachers = Teacher.objects.filter(
            available_branches=branch,
            is_active=True
        ).prefetch_related('available_branches')
        
        # Временные слоты (11:00-18:00 с шагом 1 час)
        time_slots = []
        start_time = datetime.combine(week_start.date(), branch.opening_time)
        end_time = datetime.combine(week_start.date(), branch.closing_time)
        
        while start_time < end_time:
            time_slots.append(start_time.time())
            start_time += timedelta(hours=1)
        
        # Дни недели с учетом паттернов филиала
        available_days = []
        for pattern in branch.available_patterns:
            if pattern == 'tue_thu':
                available_days.extend([1, 3])  # вторник, четверг (0=понедельник)
            elif pattern == 'wed_sat':
                available_days.extend([2, 5])  # среда, суббота
            elif pattern == 'mon_fri':
                available_days.extend([0, 4])  # понедельник, пятница
        
        available_days = list(set(available_days))  # убираем дубликаты
        
        return {
            'classrooms': classrooms,
            'teachers': teachers,
            'time_slots': time_slots,
            'available_days': available_days,
            'peak_start': branch.peak_start,
            'peak_end': branch.peak_end
        }
    
    def _schedule_regular_lessons(self, groups, available_slots: Dict, week_start: datetime) -> List[Dict]:
        """Планирование обычных занятий групп"""
        
        scheduled_lessons = []
        
        for group in groups:
            # Получаем дни для занятий группы
            group_days = group.get_schedule_days()
            
            # Планируем на каждый день недели
            for day_offset in group_days:
                lesson_date = week_start + timedelta(days=day_offset)
                lesson_datetime = datetime.combine(lesson_date.date(), group.lesson_time)
                
                # Ищем доступный кабинет и преподавателя
                classroom = self._find_available_classroom(lesson_datetime, available_slots['classrooms'])
                teacher = self._find_available_teacher(group, lesson_datetime, available_slots['teachers'])
                
                if classroom and teacher:
                    lesson_data = {
                        'group': group,
                        'teacher': teacher,
                        'datetime': lesson_datetime,
                        'classroom': classroom,
                        'lesson_type': 'regular',
                        'duration': group.lesson_duration
                    }
                    scheduled_lessons.append(lesson_data)
                    
                    # Создаем занятие в БД
                    self._create_lesson(lesson_data)
                else:
                    # Регистрируем конфликт
                    self.conflicts.append({
                        'type': 'resource_unavailable',
                        'group': group.name,
                        'datetime': lesson_datetime,
                        'missing_resource': 'classroom' if not classroom else 'teacher'
                    })
        
        return scheduled_lessons
    
    def _schedule_special_lessons(self, groups, available_slots: Dict, week_start: datetime) -> List[Dict]:
        """Планирование специальных занятий (контрольные + лексика) для Екатерины"""
        
        special_lessons = []
        ekaterina = Teacher.objects.filter(can_teach_control_lessons=True, is_director=True).first()
        
        if not ekaterina:
            logger.warning("Преподаватель для специальных занятий не найден")
            return special_lessons
        
        # Находим группы, которым нужны специальные занятия
        for group in groups:
            if group.is_unit_complete():
                current_unit = group.units.filter(status='lessons_completed').first()
                
                if current_unit and not current_unit.control_lesson_scheduled:
                    # Планируем контрольное занятие
                    control_lesson = self._schedule_control_lesson(group, ekaterina, available_slots, week_start)
                    if control_lesson:
                        special_lessons.append(control_lesson)
                        current_unit.control_lesson_scheduled = True
                        current_unit.save()
                
                if current_unit and not current_unit.vocabulary_lesson_scheduled:
                    # Планируем занятие расширенной лексики
                    vocab_lesson = self._schedule_vocabulary_lesson(group, ekaterina, available_slots, week_start)
                    if vocab_lesson:
                        special_lessons.append(vocab_lesson)
                        current_unit.vocabulary_lesson_scheduled = True
                        current_unit.save()
        
        return special_lessons
    
    def _distribute_compensation_work(self, groups, available_slots: Dict, week_start: datetime) -> List[Dict]:
        """Распределение компенсационной работы для основных преподавателей"""
        
        compensation_tasks = []
        
        # Находим преподавателей, которые временно свободны из-за спецзанятий
        for group in groups:
            if group.is_unit_complete():
                main_teacher = group.main_teacher
                
                # Создаем компенсационные задачи
                compensation_types = [
                    {
                        'type': 'homework_check',
                        'description': f'Проверка домашних заданий других групп',
                        'duration': timedelta(hours=1),
                        'rate': main_teacher.compensation_rate
                    },
                    {
                        'type': 'parent_calls', 
                        'description': f'Обзвон родителей учеников',
                        'duration': timedelta(minutes=45),
                        'rate': main_teacher.compensation_rate
                    },
                    {
                        'type': 'materials_prep',
                        'description': f'Подготовка учебных материалов',
                        'duration': timedelta(hours=1),
                        'rate': main_teacher.compensation_rate
                    }
                ]
                
                for comp_work in compensation_types:
                    # Находим свободное время для компенсационной работы
                    free_slot = self._find_free_slot_for_teacher(main_teacher, week_start, comp_work['duration'])
                    
                    if free_slot:
                        compensation_data = {
                            'teacher': main_teacher,
                            'work_type': comp_work['type'],
                            'description': comp_work['description'],
                            'scheduled_datetime': free_slot,
                            'duration': comp_work['duration'],
                            'rate_per_hour': comp_work['rate'],
                            'total_payment': self._calculate_compensation_payment(comp_work['duration'], comp_work['rate'])
                        }
                        
                        compensation_tasks.append(compensation_data)
                        
                        # Создаем в БД
                        CompensationWork.objects.create(**compensation_data)
        
        return compensation_tasks
    
    def _detect_and_resolve_conflicts(self, all_lessons: List[Dict]) -> List[Dict]:
        """Обнаружение и автоматическое разрешение конфликтов"""
        
        detected_conflicts = []
        
        # Группируем занятия по времени для поиска конфликтов
        lessons_by_time = {}
        for lesson in all_lessons:
            datetime_key = lesson['datetime']
            if datetime_key not in lessons_by_time:
                lessons_by_time[datetime_key] = []
            lessons_by_time[datetime_key].append(lesson)
        
        # Проверяем конфликты
        for datetime_slot, lessons in lessons_by_time.items():
            if len(lessons) > 1:
                # Есть несколько занятий в одно время
                conflicts = self._analyze_time_slot_conflicts(lessons, datetime_slot)
                detected_conflicts.extend(conflicts)
        
        # Автоматическое разрешение конфликтов
        for conflict in detected_conflicts:
            resolution = self._suggest_conflict_resolution(conflict)
            if resolution:
                conflict['suggested_resolution'] = resolution
        
        return detected_conflicts
    
    def _optimize_peak_time_usage(self, lessons: List[Dict], branch: Branch) -> List[Dict]:
        """Оптимизация использования пикового времени (13:00-17:00)"""
        
        optimized_lessons = []
        peak_start = branch.peak_start
        peak_end = branch.peak_end
        
        # Сортируем занятия по приоритету (важные группы в пиковое время)
        lessons_sorted = sorted(lessons, key=lambda x: self._calculate_lesson_priority(x))
        
        for lesson in lessons_sorted:
            lesson_time = lesson['datetime'].time()
            
            # Если занятие попадает в пиковое время - повышаем приоритет
            if peak_start <= lesson_time <= peak_end:
                lesson['is_peak_time'] = True
                lesson['priority_score'] = lesson.get('priority_score', 0) + 10
            
            optimized_lessons.append(lesson)
        
        return optimized_lessons
    
    def _calculate_statistics(self, regular_lessons: List, special_lessons: List, branch: Branch) -> Dict:
        """Расчет статистики по сгенерированному расписанию"""
        
        return {
            'total_regular_lessons': len(regular_lessons),
            'total_special_lessons': len(special_lessons),
            'peak_time_utilization': self._calculate_peak_utilization(regular_lessons + special_lessons, branch),
            'teacher_load_distribution': self._calculate_teacher_load_stats(regular_lessons + special_lessons),
            'classroom_utilization': self._calculate_classroom_utilization(regular_lessons + special_lessons),
            'conflicts_count': len(self.conflicts)
        }
    
    def _find_available_classroom(self, datetime: datetime, classrooms: List) -> Optional[Classroom]:
        """Поиск свободного кабинета на указанное время"""
        for classroom in classrooms:
            existing_lessons = Lesson.objects.filter(
                classroom=classroom,
                datetime=datetime,
                status__in=['scheduled', 'completed']
            )
            if not existing_lessons.exists():
                return classroom
        return None
    
    def _find_available_teacher(self, group: Group, datetime: datetime, teachers: List) -> Optional[Teacher]:
        """Поиск доступного преподавателя для группы"""
        # Сначала пробуем основного преподавателя группы
        if self._is_teacher_available(group.main_teacher, datetime):
            return group.main_teacher
        
        # Если основной недоступен, ищем замену среди доступных для филиала
        for teacher in teachers:
            if (teacher.can_work_at_branch(group.branch) and 
                self._is_teacher_available(teacher, datetime) and
                self._check_teacher_daily_load(teacher, datetime)):
                return teacher
        
        return None
    
    def _is_teacher_available(self, teacher: Teacher, datetime: datetime) -> bool:
        """Проверка доступности преподавателя"""
        weekday = datetime.weekday() + 1  # Django использует 1-7 для пн-вс
        
        # Проверяем доступность по дням недели
        if weekday not in teacher.available_weekdays:
            return False
        
        # Проверяем отсутствие других занятий в это время
        existing_lessons = Lesson.objects.filter(
            teacher=teacher,
            datetime=datetime,
            status__in=['scheduled', 'completed']
        )
        
        return not existing_lessons.exists()
    
    def _check_teacher_daily_load(self, teacher: Teacher, datetime: datetime) -> bool:
        """Проверка дневной нагрузки преподавателя"""
        day_start = datetime.replace(hour=0, minute=0, second=0)
        day_end = day_start + timedelta(days=1)
        
        daily_lessons = Lesson.objects.filter(
            teacher=teacher,
            datetime__gte=day_start,
            datetime__lt=day_end,
            status__in=['scheduled', 'completed']
        ).count()
        
        return daily_lessons < teacher.max_daily_load
    
    def _create_lesson(self, lesson_data: Dict) -> Lesson:
        """Создание занятия в базе данных"""
        # Находим или создаем юнит для группы
        group = lesson_data['group']
        current_unit = group.units.filter(status='in_progress').first()
        
        if not current_unit:
            current_unit = Unit.objects.create(
                group=group,
                unit_number=group.current_unit,
                start_date=lesson_data['datetime'].date(),
                planned_end_date=lesson_data['datetime'].date() + timedelta(weeks=3),
                status='in_progress'
            )
        
        lesson = Lesson.objects.create(
            group=group,
            unit=current_unit,
            teacher=lesson_data['teacher'],
            datetime=lesson_data['datetime'],
            classroom=lesson_data['classroom'],
            lesson_type=lesson_data['lesson_type'],
            status='scheduled'
        )
        
        # Обновляем прогресс группы
        if lesson_data['lesson_type'] == 'regular':
            group.lessons_in_current_unit += 1
            if group.lessons_in_current_unit >= 6:
                current_unit.status = 'lessons_completed'
                current_unit.save()
            group.save()
        
        return lesson
    
    def _schedule_control_lesson(self, group: Group, teacher: Teacher, available_slots: Dict, week_start: datetime) -> Optional[Dict]:
        """Планирование контрольного занятия"""
        # Ищем оптимальное время для контрольного занятия
        for day_offset in range(7):  # проверяем всю неделю
            lesson_date = week_start + timedelta(days=day_offset)
            
            # Пробуем разные временные слоты
            for time_slot in available_slots['time_slots']:
                lesson_datetime = datetime.combine(lesson_date.date(), time_slot)
                
                if self._is_teacher_available(teacher, lesson_datetime):
                    classroom = self._find_available_classroom(lesson_datetime, available_slots['classrooms'])
                    
                    if classroom:
                        lesson_data = {
                            'group': group,
                            'teacher': teacher,
                            'datetime': lesson_datetime,
                            'classroom': classroom,
                            'lesson_type': 'control',
                            'duration': timedelta(minutes=45)
                        }
                        
                        # Создаем в БД
                        self._create_lesson(lesson_data)
                        return lesson_data
        
        return None
    
    def _schedule_vocabulary_lesson(self, group: Group, teacher: Teacher, available_slots: Dict, week_start: datetime) -> Optional[Dict]:
        """Планирование занятия расширенной лексики"""
        # Аналогично контрольному занятию, но с типом 'vocabulary'
        for day_offset in range(7):
            lesson_date = week_start + timedelta(days=day_offset)
            
            for time_slot in available_slots['time_slots']:
                lesson_datetime = datetime.combine(lesson_date.date(), time_slot)
                
                if self._is_teacher_available(teacher, lesson_datetime):
                    classroom = self._find_available_classroom(lesson_datetime, available_slots['classrooms'])
                    
                    if classroom:
                        lesson_data = {
                            'group': group,
                            'teacher': teacher,
                            'datetime': lesson_datetime,
                            'classroom': classroom,
                            'lesson_type': 'vocabulary',
                            'duration': timedelta(minutes=45)
                        }
                        
                        self._create_lesson(lesson_data)
                        return lesson_data
        
        return None