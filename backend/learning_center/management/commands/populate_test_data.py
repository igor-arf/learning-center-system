# learning_center/management/commands/populate_test_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from learning_center.models import *
from datetime import datetime, timedelta, time
import random

class Command(BaseCommand):
    help = 'Populate database with test data'
    
    def handle(self, *args, **options):
        self.stdout.write('Создание тестовых данных...')
        
        # Создаем филиалы
        branch1 = Branch.objects.create(
            name='Бульвар',
            address='ул. Главная, 123',
            classrooms_count=3,
            available_patterns=['tue_thu', 'wed_sat'],
            opening_time=time(11, 0),
            closing_time=time(18, 0),
            peak_start=time(13, 0),
            peak_end=time(17, 0)
        )
        
        branch2 = Branch.objects.create(
            name='Улитка',
            address='ул. Центральная, 456',
            classrooms_count=1,
            available_patterns=['mon_fri', 'wed_sat'],
            opening_time=time(11, 0),
            closing_time=time(18, 0),
            peak_start=time(13, 0),
            peak_end=time(17, 0)
        )
        
        # Создаем кабинеты
        for i in range(1, 4):
            Classroom.objects.create(
                branch=branch1,
                number=f'A{i}',
                capacity=8,
                equipment='Интерактивная доска, проектор'
            )
        
        Classroom.objects.create(
            branch=branch2,
            number='B1',
            capacity=6,
            equipment='Телевизор, аудиосистема'
        )
        
        # Создаем пользователей и преподавателей
        teachers_data = [
            {
                'username': 'diana',
                'first_name': 'Диана',
                'last_name': 'Иванова',
                'email': 'diana@example.com',
                'branches': [branch1],
                'role': 'regular',
                'max_daily': 6,
                'weekdays': [2, 4]  # вт, чт
            },
            {
                'username': 'emilia',
                'first_name': 'Эмилия',
                'last_name': 'Петрова',
                'email': 'emilia@example.com',
                'branches': [branch1, branch2],
                'role': 'admin',
                'max_daily': 4,
                'weekdays': [1, 2, 3, 4, 5, 6]  # все дни
            },
            {
                'username': 'irina',
                'first_name': 'Ирина',
                'last_name': 'Сидорова',
                'email': 'irina@example.com',
                'branches': [branch1],
                'role': 'regular',
                'max_daily': 3,
                'weekdays': [2, 4, 6]  # вт, чт, сб
            },
            {
                'username': 'ekaterina',
                'first_name': 'Екатерина',
                'last_name': 'Директорова',
                'email': 'ekaterina@example.com',
                'branches': [branch1, branch2],
                'role': 'director',
                'max_daily': 5,
                'weekdays': [1, 2, 3, 4, 5, 6],
                'special_abilities': True
            }
        ]
        
        for teacher_data in teachers_data:
            user = User.objects.create_user(
                username=teacher_data['username'],
                first_name=teacher_data['first_name'],
                last_name=teacher_data['last_name'],
                email=teacher_data['email'],
                password='password123'
            )
            
            teacher = Teacher.objects.create(
                user=user,
                teacher_role=teacher_data['role'],
                max_daily_load=teacher_data['max_daily'],
                available_weekdays=teacher_data['weekdays'],
                base_rate_per_lesson=1000,
                special_lesson_rate=1500,
                compensation_rate=800,
                can_teach_control_lessons=teacher_data.get('special_abilities', False),
                can_teach_vocabulary_lessons=teacher_data.get('special_abilities', False),
                is_director=teacher_data['role'] == 'director',
                is_admin_teacher=teacher_data['role'] == 'admin'
            )
            
            teacher.available_branches.set(teacher_data['branches'])
        
        # Создаем учеников
        students_data = [
            {'first_name': 'Анна', 'last_name': 'Петрова', 'level': 'beginner'},
            {'first_name': 'Михаил', 'last_name': 'Сидоров', 'level': 'elementary'},
            {'first_name': 'Елена', 'last_name': 'Козлова', 'level': 'intermediate'},
            {'first_name': 'Дмитрий', 'last_name': 'Новikov', 'level': 'pre_intermediate'},
            {'first_name': 'Ольга', 'last_name': 'Федорова', 'level': 'upper_intermediate'},
            {'first_name': 'Александр', 'last_name': 'Морозов', 'level': 'advanced'},
        ]
        
        students = []
        for i, student_data in enumerate(students_data):
            student = Student.objects.create(
                first_name=student_data['first_name'],
                last_name=student_data['last_name'],
                phone=f'+7911{i:07d}',
                email=f"{student_data['first_name'].lower()}@example.com",
                level=student_data['level'],
                enrollment_date=datetime.now().date() - timedelta(days=random.randint(30, 365)),
                status='active'
            )
            students.append(student)
        
        # Создаем группы
        groups_data = [
            {
                'name': 'Beginners Morning',
                'branch': branch1,
                'level': 'beginner',
                'teacher': Teacher.objects.get(user__username='diana'),
                'pattern': 'tue_thu',
                'time': time(11, 0),
                'students': students[:3]
            },
            {
                'name': 'Elementary Evening',
                'branch': branch1,
                'level': 'elementary',
                'teacher': Teacher.objects.get(user__username='emilia'),
                'pattern': 'wed_sat',
                'time': time(16, 0),
                'students': students[1:4]
            },
            {
                'name': 'Intermediate Focus',
                'branch': branch2,
                'level': 'intermediate',
                'teacher': Teacher.objects.get(user__username='emilia'),
                'pattern': 'mon_fri',
                'time': time(14, 0),
                'students': students[2:5]
            }
        ]
        
        for group_data in groups_data:
            group = Group.objects.create(
                name=group_data['name'],
                branch=group_data['branch'],
                level=group_data['level'],
                main_teacher=group_data['teacher'],
                schedule_pattern=group_data['pattern'],
                lesson_time=group_data['time'],
                current_unit=1,
                lessons_in_current_unit=random.randint(0, 5)
            )
            group.students.set(group_data['students'])
            
            # Создаем юнит для группы
            Unit.objects.create(
                group=group,
                unit_number=1,
                start_date=datetime.now().date() - timedelta(days=14),
                planned_end_date=datetime.now().date() + timedelta(days=14),
                status='in_progress'
            )
        
        self.stdout.write(
            self.style.SUCCESS('Тестовые данные успешно созданы!')
        )

