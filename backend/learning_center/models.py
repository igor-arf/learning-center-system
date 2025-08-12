# learning_center/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime, timedelta
import enum

class UserRole(models.TextChoices):
    """Роли пользователей в системе"""
    ADMIN = 'admin', 'Администратор'
    DIRECTOR = 'director', 'Руководитель'
    TEACHER = 'teacher', 'Преподаватель'

class User(AbstractUser):
    """Расширенная модель пользователя"""
    role = models.CharField(max_length=20, choices=UserRole.choices)
    phone = models.CharField(max_length=15, blank=True)
    
class Branch(models.Model):
    """Модель филиала учебного центра"""
    name = models.CharField(max_length=100)
    address = models.TextField()
    classrooms_count = models.PositiveIntegerField()
    
    # Доступные дни для занятий (JSON поле)
    SCHEDULE_PATTERNS = [
        ('tue_thu', 'Вторник + Четверг'),
        ('wed_sat', 'Среда + Суббота'),
        ('mon_fri', 'Понедельник + Пятница'),
    ]
    
    available_patterns = models.JSONField(default=list)  # ['tue_thu', 'wed_sat']
    opening_time = models.TimeField(default='11:00')
    closing_time = models.TimeField(default='18:00')
    peak_start = models.TimeField(default='13:00')
    peak_end = models.TimeField(default='17:00')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Филиал"
        verbose_name_plural = "Филиалы"
    
    def __str__(self):
        return f"{self.name} ({self.address})"

class Classroom(models.Model):
    """Модель кабинета"""
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='classrooms')
    number = models.CharField(max_length=10)
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    equipment = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['branch', 'number']
        verbose_name = "Кабинет"
        verbose_name_plural = "Кабинеты"
    
    def __str__(self):
        return f"Кабинет {self.number} ({self.branch.name})"

class Teacher(models.Model):
    """Модель преподавателя с специфическими ограничениями"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    TEACHER_ROLES = [
        ('regular', 'Обычный преподаватель'),
        ('admin', 'Администратор'),
        ('director', 'Руководитель'),
        ('specialist', 'Специалист'),
    ]
    
    teacher_role = models.CharField(max_length=20, choices=TEACHER_ROLES, default='regular')
    
    # Ограничения по филиалам
    available_branches = models.ManyToManyField(Branch, related_name='teachers')
    
    # Ограничения нагрузки
    max_daily_load = models.PositiveIntegerField(default=8)  # максимум занятий в день
    min_weekly_load = models.PositiveIntegerField(default=0)  # минимум занятий в неделю
    preferred_load = models.PositiveIntegerField(default=20)  # предпочтительная нагрузка
    
    # Доступность по дням недели (JSON)
    available_weekdays = models.JSONField(default=list)  # [1,2,4,5] - пн,вт,чт,пт
    
    # Специальные роли (для Екатерины, Эмилии и др.)
    can_teach_control_lessons = models.BooleanField(default=False)  # контрольные занятия
    can_teach_vocabulary_lessons = models.BooleanField(default=False)  # расширенная лексика
    is_director = models.BooleanField(default=False)
    is_admin_teacher = models.BooleanField(default=False)
    
    # Финансовые настройки
    base_rate_per_lesson = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    special_lesson_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    compensation_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Преподаватель"
        verbose_name_plural = "Преподаватели"
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_teacher_role_display()})"
    
    def can_work_at_branch(self, branch):
        """Проверка доступности филиала для преподавателя"""
        return self.available_branches.filter(id=branch.id).exists()

class Student(models.Model):
    """Модель ученика"""
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    parent_contact = models.CharField(max_length=15, blank=True)  # для несовершеннолетних
    
    ENGLISH_LEVELS = [
        ('beginner', 'Beginner'),
        ('elementary', 'Elementary'),
        ('pre_intermediate', 'Pre-Intermediate'),
        ('intermediate', 'Intermediate'),
        ('upper_intermediate', 'Upper-Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    level = models.CharField(max_length=20, choices=ENGLISH_LEVELS)
    
    STUDENT_STATUS = [
        ('active', 'Активный'),
        ('paused', 'Приостановлен'),
        ('finished', 'Завершил обучение'),
        ('dropped', 'Отчислен'),
    ]
    
    status = models.CharField(max_length=20, choices=STUDENT_STATUS, default='active')
    enrollment_date = models.DateField()
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Ученик"
        verbose_name_plural = "Ученики"
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_level_display()})"

class Group(models.Model):
    """Учебная группа"""
    name = models.CharField(max_length=100)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='groups')
    level = models.CharField(max_length=20, choices=Student.ENGLISH_LEVELS)
    
    main_teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='main_groups')
    students = models.ManyToManyField(Student, related_name='groups', blank=True)
    
    # Паттерн расписания
    schedule_pattern = models.CharField(max_length=20, choices=Branch.SCHEDULE_PATTERNS)
    
    # Время занятий
    lesson_time = models.TimeField()  # время начала занятия
    lesson_duration = models.DurationField(default=timedelta(minutes=45))
    
    max_students = models.PositiveIntegerField(default=8)
    is_active = models.BooleanField(default=True)
    
    # Прогресс обучения
    current_unit = models.PositiveIntegerField(default=1)
    lessons_in_current_unit = models.PositiveIntegerField(default=0)  # от 0 до 6
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"
    
    def __str__(self):
        return f"{self.name} - {self.get_level_display()} ({self.branch.name})"
    
    @property
    def current_students_count(self):
        return self.students.filter(status='active').count()
    
    def is_unit_complete(self):
        """Проверка завершения текущего юнита"""
        return self.lessons_in_current_unit >= 6
    
    def get_schedule_days(self):
        """Возвращает дни недели для занятий"""
        patterns = {
            'tue_thu': [2, 4],  # Вторник, четверг
            'wed_sat': [3, 6],  # Среда, суббота  
            'mon_fri': [1, 5],  # Понедельник, пятница
        }
        return patterns.get(self.schedule_pattern, [])

class Unit(models.Model):
    """Учебный юнит (6 обычных занятий + 2 специальных)"""
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='units')
    unit_number = models.PositiveIntegerField()
    
    start_date = models.DateField()
    planned_end_date = models.DateField()
    actual_end_date = models.DateField(null=True, blank=True)
    
    UNIT_STATUS = [
        ('planned', 'Запланирован'),
        ('in_progress', 'В процессе'),
        ('lessons_completed', 'Основные занятия завершены'),
        ('completed', 'Полностью завершен'),
    ]
    
    status = models.CharField(max_length=20, choices=UNIT_STATUS, default='planned')
    
    # Специальные занятия
    control_lesson_scheduled = models.BooleanField(default=False)
    vocabulary_lesson_scheduled = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['group', 'unit_number']
        verbose_name = "Юнит"
        verbose_name_plural = "Юниты"
    
    def __str__(self):
        return f"Юнит {self.unit_number} - {self.group.name}"

class Lesson(models.Model):
    """Конкретное занятие"""
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='lessons')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='lessons')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='lessons')
    
    datetime = models.DateTimeField()
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='lessons')
    
    LESSON_TYPES = [
        ('regular', 'Обычное занятие'),
        ('control', 'Контрольное занятие'),
        ('vocabulary', 'Расширенная лексика'),
        ('makeup', 'Отработка'),
        ('trial', 'Пробное занятие'),
    ]
    
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES, default='regular')
    
    # Статус проведения
    STATUS_CHOICES = [
        ('scheduled', 'Запланировано'),
        ('completed', 'Проведено'),
        ('cancelled', 'Отменено'),
        ('rescheduled', 'Перенесено'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Посещаемость и материалы
    attendance_count = models.PositiveIntegerField(default=0)
    homework_assigned = models.TextField(blank=True)
    lesson_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Занятие"
        verbose_name_plural = "Занятия"
    
    def __str__(self):
        return f"{self.group.name} - {self.datetime.strftime('%d.%m.%Y %H:%M')} ({self.get_lesson_type_display()})"

class CompensationWork(models.Model):
    """Компенсационная работа для преподавателей"""
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='compensation_work')
    
    # Связь с замещаемым занятием (если есть)
    replaced_lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, null=True, blank=True)
    
    WORK_TYPES = [
        ('substitution', 'Замещение коллеги'),
        ('individual', 'Индивидуальное занятие'),
        ('conversation_club', 'Разговорный клуб'),
        ('homework_check', 'Проверка домашних заданий'),
        ('parent_calls', 'Обзвон родителей'),
        ('materials_prep', 'Подготовка материалов'),
        ('debtor_work', 'Работа с задолжниками'),
        ('administrative', 'Административная работа'),
    ]
    
    work_type = models.CharField(max_length=20, choices=WORK_TYPES)
    description = models.TextField()
    
    scheduled_datetime = models.DateTimeField()
    duration = models.DurationField(default=timedelta(minutes=45))
    
    # Оплата
    rate_per_hour = models.DecimalField(max_digits=8, decimal_places=2)
    total_payment = models.DecimalField(max_digits=8, decimal_places=2)
    
    is_completed = models.BooleanField(default=False)
    completion_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Компенсационная работа"
        verbose_name_plural = "Компенсационная работа"
    
    def __str__(self):
        return f"{self.teacher} - {self.get_work_type_display()} ({self.scheduled_datetime.strftime('%d.%m.%Y %H:%M')})"

class ScheduleConflict(models.Model):
    """Конфликты в расписании"""
    CONFLICT_TYPES = [
        ('teacher_double_booking', 'Преподаватель в двух местах'),
        ('classroom_double_booking', 'Кабинет занят'),
        ('teacher_overload', 'Превышение дневной нагрузки'),
        ('schedule_pattern_violation', 'Нарушение паттерна группы'),
        ('branch_restriction', 'Недоступный филиал для преподавателя'),
    ]
    
    conflict_type = models.CharField(max_length=30, choices=CONFLICT_TYPES)
    description = models.TextField()
    
    # Связанные объекты
    lesson1 = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='conflicts_as_lesson1')
    lesson2 = models.ForeignKey(Lesson, on_delete=models.CASCADE, null=True, blank=True, related_name='conflicts_as_lesson2')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, null=True, blank=True)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, null=True, blank=True)
    
    # Статус разрешения
    RESOLUTION_STATUS = [
        ('pending', 'Ожидает решения'),
        ('resolved', 'Решено'),
        ('ignored', 'Проигнорировано'),
    ]
    
    status = models.CharField(max_length=20, choices=RESOLUTION_STATUS, default='pending')
    resolution_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Конфликт расписания"
        verbose_name_plural = "Конфликты расписания"


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


# learning_center/services/rotation_manager.py
class RotationManager:
    """
    Менеджер системы ротации и компенсации преподавателей
    """
    
    def plan_unit_completion(self, unit_id: int) -> Dict:
        """
        Планирование завершения юнита с ротацией преподавателей
        
        При завершении юнита:
        1. Назначить Екатерину на контрольное занятие
        2. Назначить Екатерину на лексическое занятие  
        3. Найти компенсационную работу основному преподавателю
        4. Обеспечить сохранение зарплаты
        """
        try:
            unit = Unit.objects.get(id=unit_id)
            group = unit.group
            main_teacher = group.main_teacher
            
            # Находим Екатерину (руководителя)
            ekaterina = Teacher.objects.filter(
                can_teach_control_lessons=True,
                can_teach_vocabulary_lessons=True,
                is_director=True
            ).first()
            
            if not ekaterina:
                return {'status': 'error', 'message': 'Преподаватель для спецзанятий не найден'}
            
            # Планируем специальные занятия
            special_lessons = []
            
            # 1. Контрольное занятие
            control_lesson = self._schedule_special_lesson(
                unit, ekaterina, 'control', 
                description='Контрольное занятие по завершении юнита'
            )
            if control_lesson:
                special_lessons.append(control_lesson)
            
            # 2. Занятие расширенной лексики
            vocab_lesson = self._schedule_special_lesson(
                unit, ekaterina, 'vocabulary',
                description='Расширенная лексика после контрольной работы'
            )
            if vocab_lesson:
                special_lessons.append(vocab_lesson)
            
            # 3. Компенсационная работа для основного преподавателя
            compensation_work = self.distribute_compensation_work(
                main_teacher.id, 
                self._get_teacher_free_slots(main_teacher, special_lessons)
            )
            
            # 4. Обновляем статус юнита
            unit.status = 'lessons_completed'
            unit.control_lesson_scheduled = bool(control_lesson)
            unit.vocabulary_lesson_scheduled = bool(vocab_lesson)
            unit.save()
            
            return {
                'status': 'success',
                'special_lessons': special_lessons,
                'compensation_work': compensation_work,
                'main_teacher_guaranteed_income': self._calculate_guaranteed_income(main_teacher, unit)
            }
            
        except Exception as e:
            logger.error(f"Ошибка планирования завершения юнита {unit_id}: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def distribute_compensation_work(self, teacher_id: int, free_slots: List[datetime]) -> List[Dict]:
        """
        Распределение компенсационной работы
        
        Типы компенсационной работы:
        - Подмена заболевших коллег
        - Индивидуальные занятия
        - Разговорные клубы
        - Проверка домашних заданий других групп
        - Обзвон родителей
        - Подготовка учебных материалов
        - Работа с задолжниками
        """
        try:
            teacher = Teacher.objects.get(id=teacher_id)
            compensation_tasks = []
            
            # Определяем типы доступной компенсационной работы
            available_work_types = [
                {
                    'type': 'substitution',
                    'description': 'Замещение заболевшего коллеги',
                    'priority': 1,
                    'duration': 45,
                    'rate_multiplier': 1.2
                },
                {
                    'type': 'individual',
                    'description': 'Индивидуальное занятие с отстающим учеником',
                    'priority': 2,
                    'duration': 45,
                    'rate_multiplier': 1.5
                },
                {
                    'type': 'conversation_club',
                    'description': 'Ведение разговорного клуба',
                    'priority': 3,
                    'duration': 60,
                    'rate_multiplier': 1.1
                },
                {
                    'type': 'homework_check',
                    'description': 'Проверка домашних заданий других групп',
                    'priority': 4,
                    'duration': 60,
                    'rate_multiplier': 0.8
                },
                {
                    'type': 'parent_calls',
                    'description': 'Обзвон родителей по успеваемости',
                    'priority': 5,
                    'duration': 30,
                    'rate_multiplier': 0.9
                },
                {
                    'type': 'materials_prep',
                    'description': 'Подготовка учебных материалов',
                    'priority': 6,
                    'duration': 60,
                    'rate_multiplier': 1.0
                }
            ]
            
            # Распределяем работу по свободным слотам
            for slot in free_slots[:3]:  # максимум 3 компенсационные задачи
                work_type = available_work_types[len(compensation_tasks) % len(available_work_types)]
                
                compensation_data = {
                    'teacher': teacher,
                    'work_type': work_type['type'],
                    'description': work_type['description'],
                    'scheduled_datetime': slot,
                    'duration': timedelta(minutes=work_type['duration']),
                    'rate_per_hour': teacher.base_rate_per_lesson * work_type['rate_multiplier'],
                    'total_payment': self._calculate_compensation_payment(
                        work_type['duration'], 
                        teacher.base_rate_per_lesson * work_type['rate_multiplier']
                    ),
                    'is_completed': False
                }
                
                # Создаем в БД
                comp_work = CompensationWork.objects.create(**compensation_data)
                compensation_tasks.append(compensation_data)
            
            return compensation_tasks
            
        except Exception as e:
            logger.error(f"Ошибка распределения компенсационной работы для преподавателя {teacher_id}: {str(e)}")
            return []


# learning_center/services/conflict_resolver.py
class ConflictResolver:
    """
    Умный анализатор и разрешитель конфликтов в расписании
    """
    
    def detect_conflicts(self, schedule_data: List[Dict]) -> List[Dict]:
        """
        Обнаружение всех типов конфликтов в расписании
        
        Типы конфликтов:
        1. Двойное бронирование кабинета
        2. Преподаватель в двух местах одновременно
        3. Превышение дневной нагрузки преподавателя
        4. Нарушение паттерна занятий группы
        5. Занятие в недоступном филиале для преподавателя
        """
        conflicts = []
        
        # Группируем данные для анализа
        lessons_by_time = {}
        lessons_by_teacher = {}
        lessons_by_classroom = {}
        
        for lesson_data in schedule_data:
            datetime_key = lesson_data['datetime']
            teacher_key = lesson_data['teacher'].id
            classroom_key = lesson_data['classroom'].id
            
            # Группировка по времени
            if datetime_key not in lessons_by_time:
                lessons_by_time[datetime_key] = []
            lessons_by_time[datetime_key].append(lesson_data)
            
            # Группировка по преподавателям
            if teacher_key not in lessons_by_teacher:
                lessons_by_teacher[teacher_key] = []
            lessons_by_teacher[teacher_key].append(lesson_data)
            
            # Группировка по кабинетам
            if classroom_key not in lessons_by_classroom:
                lessons_by_classroom[classroom_key] = []
            lessons_by_classroom[classroom_key].append(lesson_data)
        
        # 1. Конфликты двойного бронирования кабинетов
        for datetime_slot, lessons in lessons_by_time.items():
            classroom_bookings = {}
            for lesson in lessons:
                classroom_id = lesson['classroom'].id
                if classroom_id not in classroom_bookings:
                    classroom_bookings[classroom_id] = []
                classroom_bookings[classroom_id].append(lesson)
            
            for classroom_id, classroom_lessons in classroom_bookings.items():
                if len(classroom_lessons) > 1:
                    conflicts.append({
                        'type': 'classroom_double_booking',
                        'datetime': datetime_slot,
                        'classroom': classroom_lessons[0]['classroom'],
                        'conflicting_lessons': classroom_lessons,
                        'severity': 'high',
                        'description': f'Кабинет {classroom_lessons[0]["classroom"]} забронирован для {len(classroom_lessons)} занятий одновременно'
                    })
        
        # 2. Конфликты преподавателей (двойное бронирование)
        for datetime_slot, lessons in lessons_by_time.items():
            teacher_bookings = {}
            for lesson in lessons:
                teacher_id = lesson['teacher'].id
                if teacher_id not in teacher_bookings:
                    teacher_bookings[teacher_id] = []
                teacher_bookings[teacher_id].append(lesson)
            
            for teacher_id, teacher_lessons in teacher_bookings.items():
                if len(teacher_lessons) > 1:
                    conflicts.append({
                        'type': 'teacher_double_booking',
                        'datetime': datetime_slot,
                        'teacher': teacher_lessons[0]['teacher'],
                        'conflicting_lessons': teacher_lessons,
                        'severity': 'critical',
                        'description': f'Преподаватель {teacher_lessons[0]["teacher"]} назначен на {len(teacher_lessons)} занятий одновременно'
                    })
        
        # 3. Превышение дневной нагрузки
        for teacher_id, teacher_lessons in lessons_by_teacher.items():
            daily_loads = {}
            for lesson in teacher_lessons:
                date_key = lesson['datetime'].date()
                if date_key not in daily_loads:
                    daily_loads[date_key] = []
                daily_loads[date_key].append(lesson)
            
            teacher = teacher_lessons[0]['teacher']
            for date, daily_lessons in daily_loads.items():
                if len(daily_lessons) > teacher.max_daily_load:
                    conflicts.append({
                        'type': 'teacher_overload',
                        'date': date,
                        'teacher': teacher,
                        'actual_load': len(daily_lessons),
                        'max_load': teacher.max_daily_load,
                        'severity': 'medium',
                        'description': f'Превышение дневной нагрузки преподавателя {teacher} ({len(daily_lessons)} из {teacher.max_daily_load})'
                    })
        
        return conflicts
    
    def suggest_solutions(self, conflicts: List[Dict]) -> List[Dict]:
        """
        Автоматические предложения решений для конфликтов
        
        Автоматические решения:
        - Перестановка на свободное время
        - Замена преподавателя
        - Перенос в другой кабинет
        - Изменение дня недели (в рамках паттерна)
        """
        solutions = []
        
        for conflict in conflicts:
            conflict_solutions = []
            
            if conflict['type'] == 'classroom_double_booking':
                # Решения для конфликта кабинетов
                conflict_solutions.extend(self._suggest_classroom_solutions(conflict))
            
            elif conflict['type'] == 'teacher_double_booking':
                # Решения для конфликта преподавателей
                conflict_solutions.extend(self._suggest_teacher_solutions(conflict))
            
            elif conflict['type'] == 'teacher_overload':
                # Решения для перегрузки преподавателя
                conflict_solutions.extend(self._suggest_load_redistribution(conflict))
            
            conflict['suggested_solutions'] = conflict_solutions
            solutions.append(conflict)
        
        return solutions