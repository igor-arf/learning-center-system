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
        fields = "__all__"

    def get_classrooms_count_actual(self, obj):
        return obj.classrooms.filter(is_active=True).count()

    def get_active_groups_count(self, obj):
        return obj.groups.filter(is_active=True).count()


class ClassroomSerializer(serializers.ModelSerializer):
    """Сериализатор кабинета"""

    branch_name = serializers.CharField(source="branch.name", read_only=True)
    current_occupancy = serializers.SerializerMethodField()

    class Meta:
        model = Classroom
        fields = "__all__"

    def get_current_occupancy(self, obj):
        # Текущая занятость кабинета на сегодня
        today = datetime.now().date()
        lessons_today = obj.lessons.filter(
            datetime__date=today, status="scheduled"
        ).count()
        return lessons_today


class TeacherSerializer(serializers.ModelSerializer):
    """Сериализатор преподавателя"""

    full_name = serializers.CharField(source="user.get_full_name", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    available_branches_names = serializers.StringRelatedField(
        source="available_branches", many=True, read_only=True
    )
    current_weekly_load = serializers.SerializerMethodField()
    upcoming_lessons = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = "__all__"

    def get_current_weekly_load(self, obj):
        # Текущая недельная нагрузка
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        weekly_lessons = obj.lessons.filter(
            datetime__date__gte=week_start,
            datetime__date__lte=week_end,
            status__in=["scheduled", "completed"],
        ).count()

        return weekly_lessons

    def get_upcoming_lessons(self, obj):
        # Ближайшие занятия
        upcoming = obj.lessons.filter(
            datetime__gte=datetime.now(), status="scheduled"
        ).order_by("datetime")[:5]

        return [
            {
                "id": lesson.id,
                "group": lesson.group.name,
                "datetime": lesson.datetime,
                "classroom": str(lesson.classroom),
                "lesson_type": lesson.get_lesson_type_display(),
            }
            for lesson in upcoming
        ]


class StudentSerializer(serializers.ModelSerializer):
    """Сериализатор ученика"""

    groups_info = serializers.SerializerMethodField()
    attendance_rate = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = "__all__"

    def get_groups_info(self, obj):
        return [
            {
                "id": group.id,
                "name": group.name,
                "level": group.get_level_display(),
                "branch": group.branch.name,
                "teacher": str(group.main_teacher),
            }
            for group in obj.groups.filter(is_active=True)
        ]

    def get_attendance_rate(self, obj):
        # Расчет посещаемости за последний месяц
        month_ago = datetime.now().date() - timedelta(days=30)
        total_lessons = Lesson.objects.filter(
            group__students=obj, datetime__date__gte=month_ago, status="completed"
        ).count()

        if total_lessons == 0:
            return 0

        # Здесь нужна дополнительная модель для отметок посещаемости
        # Пока возвращаем заглушку
        return 85  # %


class GroupDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор группы"""

    students_info = StudentSerializer(source="students", many=True, read_only=True)
    teacher_info = TeacherSerializer(source="main_teacher", read_only=True)
    branch_info = BranchSerializer(source="branch", read_only=True)
    current_unit_info = serializers.SerializerMethodField()
    next_lessons = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = "__all__"

    def get_current_unit_info(self, obj):
        current_unit = obj.units.filter(status="in_progress").first()
        if current_unit:
            return {
                "unit_number": current_unit.unit_number,
                "lessons_completed": obj.lessons_in_current_unit,
                "lessons_remaining": 6 - obj.lessons_in_current_unit,
                "needs_special_lessons": obj.is_unit_complete(),
            }
        return None

    def get_next_lessons(self, obj):
        upcoming = obj.lessons.filter(
            datetime__gte=datetime.now(), status="scheduled"
        ).order_by("datetime")[:3]

        return [
            {
                "datetime": lesson.datetime,
                "teacher": str(lesson.teacher),
                "classroom": str(lesson.classroom),
                "lesson_type": lesson.get_lesson_type_display(),
            }
            for lesson in upcoming
        ]


class LessonSerializer(serializers.ModelSerializer):
    """Сериализатор занятия"""

    group_name = serializers.CharField(source="group.name", read_only=True)
    teacher_name = serializers.CharField(
        source="teacher.user.get_full_name", read_only=True
    )
    classroom_info = serializers.CharField(source="classroom.__str__", read_only=True)
    duration_minutes = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = "__all__"

    def get_duration_minutes(self, obj):
        if obj.group and obj.group.lesson_duration:
            return int(obj.group.lesson_duration.total_seconds() / 60)
        return 45
