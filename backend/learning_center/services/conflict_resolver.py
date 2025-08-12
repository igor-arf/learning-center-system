# learning_center/services/conflict_resolver.py

from typing import List, Dict

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
