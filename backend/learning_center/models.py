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
