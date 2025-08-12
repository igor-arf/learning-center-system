# learning_center/serializers.py
from rest_framework import serializers
from .models import *
from datetime import datetime, timedelta

class BranchSerializer(serializers.ModelSerializer):
    """Сериализатор филиала"""
    classrooms_count_actual = serializers.SerializerMethodField()
    active_groups_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Branch
        fields = '__all__'
    
    def get_classrooms_count_actual(self, obj):
        return obj.classrooms.filter(is_active=True).count()
    
    def get_active_groups_count(self, obj):
        return obj.groups.filter(is_active=True).count()

class ClassroomSerializer(serializers.ModelSerializer):
    """Сериализатор кабинета"""
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    current_occupancy = serializers.SerializerMethodField()
    
    class Meta:
        model = Classroom
        fields = '__all__'
    
    def get_current_occupancy(self, obj):
        # Текущая занятость кабинета на сегодня
        today = datetime.now().date()
        lessons_today = obj.lessons.filter(
            datetime__date=today,
            status='scheduled'
        ).count()
        return lessons_today

class TeacherSerializer(serializers.ModelSerializer):
    """Сериализатор преподавателя"""
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    available_branches_names = serializers.StringRelatedField(source='available_branches', many=True, read_only=True)
    current_weekly_load = serializers.SerializerMethodField()
    upcoming_lessons = serializers.SerializerMethodField()
    
    class Meta:
        model = Teacher
        fields = '__all__'
    
    def get_current_weekly_load(self, obj):
        # Текущая недельная нагрузка
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        weekly_lessons = obj.lessons.filter(
            datetime__date__gte=week_start,
            datetime__date__lte=week_end,
            status__in=['scheduled', 'completed']
        ).count()
        
        return weekly_lessons
    
    def get_upcoming_lessons(self, obj):
        # Ближайшие занятия
        upcoming = obj.lessons.filter(
            datetime__gte=datetime.now(),
            status='scheduled'
        ).order_by('datetime')[:5]
        
        return [{
            'id': lesson.id,
            'group': lesson.group.name,
            'datetime': lesson.datetime,
            'classroom': str(lesson.classroom),
            'lesson_type': lesson.get_lesson_type_display()
        } for lesson in upcoming]

class StudentSerializer(serializers.ModelSerializer):
    """Сериализатор ученика"""
    groups_info = serializers.SerializerMethodField()
    attendance_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = '__all__'
    
    def get_groups_info(self, obj):
        return [{
            'id': group.id,
            'name': group.name,
            'level': group.get_level_display(),
            'branch': group.branch.name,
            'teacher': str(group.main_teacher)
        } for group in obj.groups.filter(is_active=True)]
    
    def get_attendance_rate(self, obj):
        # Расчет посещаемости за последний месяц
        month_ago = datetime.now().date() - timedelta(days=30)
        total_lessons = Lesson.objects.filter(
            group__students=obj,
            datetime__date__gte=month_ago,
            status='completed'
        ).count()
        
        if total_lessons == 0:
            return 0
        
        # Здесь нужна дополнительная модель для отметок посещаемости
        # Пока возвращаем заглушку
        return 85  # %

class GroupDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор группы"""
    students_info = StudentSerializer(source='students', many=True, read_only=True)
    teacher_info = TeacherSerializer(source='main_teacher', read_only=True)
    branch_info = BranchSerializer(source='branch', read_only=True)
    current_unit_info = serializers.SerializerMethodField()
    next_lessons = serializers.SerializerMethodField()
    
    class Meta:
        model = Group
        fields = '__all__'
    
    def get_current_unit_info(self, obj):
        current_unit = obj.units.filter(status='in_progress').first()
        if current_unit:
            return {
                'unit_number': current_unit.unit_number,
                'lessons_completed': obj.lessons_in_current_unit,
                'lessons_remaining': 6 - obj.lessons_in_current_unit,
                'needs_special_lessons': obj.is_unit_complete()
            }
        return None
    
    def get_next_lessons(self, obj):
        upcoming = obj.lessons.filter(
            datetime__gte=datetime.now(),
            status='scheduled'
        ).order_by('datetime')[:3]
        
        return [{
            'datetime': lesson.datetime,
            'teacher': str(lesson.teacher),
            'classroom': str(lesson.classroom),
            'lesson_type': lesson.get_lesson_type_display()
        } for lesson in upcoming]

class LessonSerializer(serializers.ModelSerializer):
    """Сериализатор занятия"""
    group_name = serializers.CharField(source='group.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    classroom_info = serializers.CharField(source='classroom.__str__', read_only=True)
    duration_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = '__all__'
    
    def get_duration_minutes(self, obj):
        if obj.group and obj.group.lesson_duration:
            return int(obj.group.lesson_duration.total_seconds() / 60)
        return 45


# learning_center/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg
from datetime import datetime, timedelta
from .services.schedule_generator import ScheduleGenerator
from .services.rotation_manager import RotationManager
from .services.conflict_resolver import ConflictResolver
import logging

logger = logging.getLogger(__name__)

class BranchViewSet(viewsets.ModelViewSet):
    """ViewSet для управления филиалами"""
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Статистика по филиалу"""
        branch = self.get_object()
        
        stats = {
            'classrooms_total': branch.classrooms.count(),
            'classrooms_active': branch.classrooms.filter(is_active=True).count(),
            'groups_total': branch.groups.count(),
            'groups_active': branch.groups.filter(is_active=True).count(),
            'teachers_available': branch.teachers.filter(is_active=True).count(),
            'students_total': sum(group.current_students_count for group in branch.groups.filter(is_active=True)),
            'lessons_this_week': self._get_weekly_lessons_count(branch),
            'utilization_rate': self._calculate_branch_utilization(branch)
        }
        
        return Response(stats)
    
    def _get_weekly_lessons_count(self, branch):
        """Количество занятий на этой неделе"""
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        return Lesson.objects.filter(
            classroom__branch=branch,
            datetime__date__gte=week_start,
            datetime__date__lte=week_end,
            status__in=['scheduled', 'completed']
        ).count()
    
    def _calculate_branch_utilization(self, branch):
        """Расчет загруженности филиала"""
        # Упрощенный расчет - отношение занятых слотов к общему количеству
        total_slots = branch.classrooms_count * 8 * 7  # кабинеты * часы в день * дни в неделю
        used_slots = self._get_weekly_lessons_count(branch)
        
        if total_slots == 0:
            return 0
        
        return round((used_slots / total_slots) * 100, 2)

class TeacherViewSet(viewsets.ModelViewSet):
    """ViewSet для управления преподавателями"""
    queryset = Teacher.objects.select_related('user').prefetch_related('available_branches')
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Фильтрация по филиалу
        branch_id = self.request.query_params.get('branch', None)
        if branch_id:
            queryset = queryset.filter(available_branches__id=branch_id)
        
        # Фильтрация по активности
        is_active = self.request.query_params.get('active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def schedule(self, request, pk=None):
        """Расписание преподавателя"""
        teacher = self.get_object()
        
        # Параметры периода
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date:
            start_date = datetime.now().date()
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if not end_date:
            end_date = start_date + timedelta(days=7)
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Получаем занятия и компенсационную работу
        lessons = teacher.lessons.filter(
            datetime__date__gte=start_date,
            datetime__date__lte=end_date,
            status__in=['scheduled', 'completed']
        ).order_by('datetime')
        
        compensation_work = teacher.compensation_work.filter(
            scheduled_datetime__date__gte=start_date,
            scheduled_datetime__date__lte=end_date
        ).order_by('scheduled_datetime')
        
        schedule_data = {
            'lessons': LessonSerializer(lessons, many=True).data,
            'compensation_work': [{
                'id': work.id,
                'work_type': work.get_work_type_display(),
                'description': work.description,
                'datetime': work.scheduled_datetime,
                'duration_minutes': int(work.duration.total_seconds() / 60),
                'payment': work.total_payment,
                'is_completed': work.is_completed
            } for work in compensation_work],
            'total_hours': self._calculate_total_hours(lessons, compensation_work),
            'estimated_income': self._calculate_estimated_income(teacher, lessons, compensation_work)
        }
        
        return Response(schedule_data)
    
    @action(detail=True, methods=['post'])
    def assign_compensation(self, request, pk=None):
        """Назначение компенсационной работы"""
        teacher = self.get_object()
        
        work_type = request.data.get('work_type')
        description = request.data.get('description')
        scheduled_datetime = request.data.get('scheduled_datetime')
        duration_minutes = request.data.get('duration_minutes', 45)
        
        if not all([work_type, description, scheduled_datetime]):
            return Response(
                {'error': 'Необходимые поля: work_type, description, scheduled_datetime'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            scheduled_datetime = datetime.fromisoformat(scheduled_datetime.replace('Z', '+00:00'))
            duration = timedelta(minutes=duration_minutes)
            
            compensation = CompensationWork.objects.create(
                teacher=teacher,
                work_type=work_type,
                description=description,
                scheduled_datetime=scheduled_datetime,
                duration=duration,
                rate_per_hour=teacher.compensation_rate,
                total_payment=self._calculate_compensation_payment(duration, teacher.compensation_rate)
            )
            
            return Response({
                'id': compensation.id,
                'message': 'Компенсационная работа назначена успешно'
            })
            
        except Exception as e:
            return Response(
                {'error': f'Ошибка назначения работы: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _calculate_total_hours(self, lessons, compensation_work):
        """Расчет общего количества часов"""
        lesson_hours = len(lessons) * 0.75  # 45 минут на занятие
        comp_hours = sum(work.duration.total_seconds() / 3600 for work in compensation_work)
        return round(lesson_hours + comp_hours, 2)
    
    def _calculate_estimated_income(self, teacher, lessons, compensation_work):
        """Расчет ожидаемого дохода"""
        lesson_income = len(lessons) * teacher.base_rate_per_lesson
        comp_income = sum(work.total_payment for work in compensation_work)
        return float(lesson_income + comp_income)
    
    def _calculate_compensation_payment(self, duration, rate_per_hour):
        """Расчет оплаты за компенсационную работу"""
        hours = duration.total_seconds() / 3600
        return rate_per_hour * hours

class StudentViewSet(viewsets.ModelViewSet):
    """ViewSet для управления учениками"""
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Фильтрация по статусу
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Фильтрация по уровню
        level_filter = self.request.query_params.get('level', None)
        if level_filter:
            queryset = queryset.filter(level=level_filter)
        
        # Поиск по имени
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )
        
        return queryset.order_by('last_name', 'first_name')
    
    @action(detail=True, methods=['post'])
    def enroll_in_group(self, request, pk=None):
        """Записать ученика в группу"""
        student = self.get_object()
        group_id = request.data.get('group_id')
        
        if not group_id:
            return Response(
                {'error': 'Необходимо указать group_id'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            group = Group.objects.get(id=group_id)
            
            # Проверяем совместимость уровня
            if student.level != group.level:
                return Response(
                    {'error': 'Уровень ученика не соответствует уровню группы'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Проверяем наличие мест
            if group.current_students_count >= group.max_students:
                return Response(
                    {'error': 'В группе нет свободных мест'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Записываем в группу
            group.students.add(student)
            student.status = 'active'
            student.save()
            
            return Response({
                'message': f'Ученик {student} успешно записан в группу {group.name}'
            })
            
        except Group.DoesNotExist:
            return Response(
                {'error': 'Группа не найдена'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def attendance_report(self, request, pk=None):
        """Отчет по посещаемости ученика"""
        student = self.get_object()
        
        # Параметры периода
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date:
            start_date = datetime.now().date() - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if not end_date:
            end_date = datetime.now().date()
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Получаем занятия ученика
        lessons = Lesson.objects.filter(
            group__students=student,
            datetime__date__gte=start_date,
            datetime__date__lte=end_date,
            status='completed'
        ).order_by('datetime')
        
        # Здесь нужна модель для отметок посещаемости
        # Пока возвращаем заглушку
        report_data = {
            'total_lessons': lessons.count(),
            'attended_lessons': int(lessons.count() * 0.85),  # 85% посещаемость
            'attendance_rate': 85.0,
            'lessons_by_group': {}
        }
        
        return Response(report_data)

class GroupViewSet(viewsets.ModelViewSet):
    """ViewSet для управления группами"""
    queryset = Group.objects.select_related('branch', 'main_teacher__user').prefetch_related('students')
    serializer_class = GroupDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Фильтрация по филиалу
        branch_id = self.request.query_params.get('branch', None)
        if branch_id:
            queryset = queryset.filter(branch__id=branch_id)
        
        # Фильтрация по активности
        is_active = self.request.query_params.get('active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('branch__name', 'name')
    
    @action(detail=True, methods=['post'])
    def complete_unit(self, request, pk=None):
        """Завершение текущего юнита группы"""
        group = self.get_object()
        
        if not group.is_unit_complete():
            return Response(
                {'error': 'Юнит еще не завершен (необходимо 6 занятий)'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Используем RotationManager для планирования завершения юнита
            rotation_manager = RotationManager()
            current_unit = group.units.filter(status='in_progress').first()
            
            if not current_unit:
                return Response(
                    {'error': 'Активный юнит не найден'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            result = rotation_manager.plan_unit_completion(current_unit.id)
            
            if result['status'] == 'success':
                # Начинаем новый юнит
                group.current_unit += 1
                group.lessons_in_current_unit = 0
                group.save()
                
                return Response({
                    'message': 'Юнит успешно завершен, запланированы специальные занятия',
                    'special_lessons': result.get('special_lessons', []),
                    'compensation_work': result.get('compensation_work', []),
                    'new_unit_number': group.current_unit
                })
            else:
                return Response(
                    {'error': result.get('message', 'Ошибка завершения юнита')}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {'error': f'Ошибка завершения юнита: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def progress_report(self, request, pk=None):
        """Отчет по прогрессу группы"""
        group = self.get_object()
        
        # Статистика по текущему юниту
        current_unit = group.units.filter(status='in_progress').first()
        completed_units = group.units.filter(status='completed').count()
        
        # Посещаемость группы
        total_lessons = group.lessons.filter(status='completed').count()
        avg_attendance = group.lessons.filter(status='completed').aggregate(
            avg=Avg('attendance_count')
        )['avg'] or 0
        
        report_data = {
            'group_info': {
                'name': group.name,
                'level': group.get_level_display(),
                'students_count': group.current_students_count,
                'teacher': str(group.main_teacher)
            },
            'progress': {
                'current_unit': group.current_unit,
                'lessons_in_current_unit': group.lessons_in_current_unit,
                'lessons_remaining_in_unit': 6 - group.lessons_in_current_unit,
                'completed_units': completed_units,
                'needs_special_lessons': group.is_unit_complete()
            },
            'attendance': {
                'total_lessons_completed': total_lessons,
                'average_attendance': round(avg_attendance, 1),
                'attendance_rate': round((avg_attendance / group.current_students_count) * 100, 1) if group.current_students_count > 0 else 0
            }
        }
        
        return Response(report_data)

class ScheduleViewSet(viewsets.ViewSet):
    """ViewSet для управления расписанием"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """Получение календарного расписания"""
        # Параметры запроса
        branch_id = request.query_params.get('branch')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        teacher_id = request.query_params.get('teacher')
        group_id = request.query_params.get('group')
        
        # Установка периода по умолчанию (текущая неделя)
        if not start_date:
            today = datetime.now().date()
            start_date = today - timedelta(days=today.weekday())
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if not end_date:
            end_date = start_date + timedelta(days=6)
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Базовый запрос
        lessons = Lesson.objects.select_related(
            'group__branch', 'teacher__user', 'classroom'
        ).filter(
            datetime__date__gte=start_date,
            datetime__date__lte=end_date,
            status__in=['scheduled', 'completed']
        )
        
        # Применение фильтров
        if branch_id:
            lessons = lessons.filter(classroom__branch__id=branch_id)
        
        if teacher_id:
            lessons = lessons.filter(teacher__id=teacher_id)
        
        if group_id:
            lessons = lessons.filter(group__id=group_id)
        
        # Сериализация данных
        calendar_data = []
        for lesson in lessons:
            calendar_data.append({
                'id': lesson.id,
                'title': f"{lesson.group.name} - {lesson.get_lesson_type_display()}",
                'start': lesson.datetime.isoformat(),
                'end': (lesson.datetime + lesson.group.lesson_duration).isoformat(),
                'group': {
                    'id': lesson.group.id,
                    'name': lesson.group.name,
                    'level': lesson.group.get_level_display()
                },
                'teacher': {
                    'id': lesson.teacher.id,
                    'name': lesson.teacher.user.get_full_name() or lesson.teacher.user.username
                },
                'classroom': {
                    'id': lesson.classroom.id,
                    'name': str(lesson.classroom),
                    'branch': lesson.classroom.branch.name
                },
                'lesson_type': lesson.lesson_type,
                'status': lesson.status,
                'color': self._get_lesson_color(lesson)
            })
        
        return Response({
            'lessons': calendar_data,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        })
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Автоматическая генерация расписания"""
        branch_id = request.data.get('branch_id')
        week_start = request.data.get('week_start')
        
        if not branch_id:
            return Response(
                {'error': 'Необходимо указать branch_id'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            if week_start:
                week_start = datetime.strptime(week_start, '%Y-%m-%d')
            else:
                today = datetime.now()
                week_start = today - timedelta(days=today.weekday())
            
            # Используем ScheduleGenerator
            generator = ScheduleGenerator()
            result = generator.generate_schedule(branch_id, week_start)
            
            if result['status'] == 'success':
                return Response({
                    'message': 'Расписание успешно сгенерировано',
                    'statistics': result['statistics'],
                    'conflicts': result['conflicts'],
                    'generated_lessons_count': len(result['regular_lessons']) + len(result['special_lessons'])
                })
            else:
                return Response(
                    {'error': result.get('message', 'Ошибка генерации расписания')}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Ошибка генерации расписания: {str(e)}")
            return Response(
                {'error': f'Ошибка генерации: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def conflicts(self, request):
        """Получение конфликтов в расписании"""
        branch_id = request.query_params.get('branch')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Установка периода по умолчанию
        if not start_date:
            today = datetime.now().date()
            start_date = today - timedelta(days=today.weekday())
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if not end_date:
            end_date = start_date + timedelta(days=6)
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Получаем занятия для анализа
        lessons = Lesson.objects.select_related(
            'group', 'teacher', 'classroom'
        ).filter(
            datetime__date__gte=start_date,
            datetime__date__lte=end_date,
            status='scheduled'
        )
        
        if branch_id:
            lessons = lessons.filter(classroom__branch__id=branch_id)
        
        # Преобразуем в формат для ConflictResolver
        lesson_data = []
        for lesson in lessons:
            lesson_data.append({
                'datetime': lesson.datetime,
                'teacher': lesson.teacher,
                'classroom': lesson.classroom,
                'group': lesson.group,
                'lesson': lesson
            })
        
        # Используем ConflictResolver
        resolver = ConflictResolver()
        conflicts = resolver.detect_conflicts(lesson_data)
        conflicts_with_solutions = resolver.suggest_solutions(conflicts)
        
        return Response({
            'conflicts': conflicts_with_solutions,
            'total_conflicts': len(conflicts_with_solutions),
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        })
    
    def _get_lesson_color(self, lesson):
        """Определение цвета занятия для календаря"""
        color_map = {
            'regular': '#3498db',      # синий
            'control': '#e74c3c',      # красный
            'vocabulary': '#f39c12',   # оранжевый
            'makeup': '#95a5a6',       # серый
            'trial': '#2ecc71'         # зеленый
        }
        return color_map.get(lesson.lesson_type, '#3498db')


# learning_center/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'branches', BranchViewSet)
router.register(r'teachers', TeacherViewSet)
router.register(r'students', StudentViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'schedule', ScheduleViewSet, basename='schedule')

urlpatterns = [
    path('api/', include(router.urls)),
]