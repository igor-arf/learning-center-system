# learning_center/services/rotation_manager.py

from typing import Dict, List
from datetime import datetime

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
