# learning_center/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import *

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'classrooms_count', 'get_active_groups', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'address']
    
    def get_active_groups(self, obj):
        return obj.groups.filter(is_active=True).count()
    get_active_groups.short_description = 'Активные группы'

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ['number', 'branch', 'capacity', 'is_active']
    list_filter = ['branch', 'is_active']
    search_fields = ['number', 'branch__name']

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'teacher_role', 'get_branches', 'max_daily_load', 'is_active']
    list_filter = ['teacher_role', 'is_active', 'available_branches']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    filter_horizontal = ['available_branches']
    
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = 'Имя'
    
    def get_branches(self, obj):
        return ', '.join([branch.name for branch in obj.available_branches.all()])
    get_branches.short_description = 'Филиалы'

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'level', 'status', 'phone', 'enrollment_date']
    list_filter = ['status', 'level', 'enrollment_date']
    search_fields = ['first_name', 'last_name', 'phone', 'email']
    date_hierarchy = 'enrollment_date'

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'branch', 'level', 'main_teacher', 'current_students_count', 'is_active']
    list_filter = ['branch', 'level', 'is_active', 'schedule_pattern']
    search_fields = ['name', 'main_teacher__user__first_name', 'main_teacher__user__last_name']
    filter_horizontal = ['students']
    
    def current_students_count(self, obj):
        return obj.current_students_count
    current_students_count.short_description = 'Учеников'

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['group', 'unit_number', 'status', 'start_date', 'planned_end_date', 'control_lesson_scheduled']
    list_filter = ['status', 'control_lesson_scheduled', 'vocabulary_lesson_scheduled']
    search_fields = ['group__name']
    date_hierarchy = 'start_date'

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['group', 'teacher', 'datetime', 'classroom', 'lesson_type', 'status', 'attendance_count']
    list_filter = ['lesson_type', 'status', 'datetime', 'classroom__branch']
    search_fields = ['group__name', 'teacher__user__first_name', 'teacher__user__last_name']
    date_hierarchy = 'datetime'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'group', 'teacher__user', 'classroom__branch'
        )

@admin.register(CompensationWork)
class CompensationWorkAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'work_type', 'scheduled_datetime', 'total_payment', 'is_completed']
    list_filter = ['work_type', 'is_completed', 'scheduled_datetime']
    search_fields = ['teacher__user__first_name', 'teacher__user__last_name', 'description']
    date_hierarchy = 'scheduled_datetime'

@admin.register(ScheduleConflict)
class ScheduleConflictAdmin(admin.ModelAdmin):
    list_display = ['conflict_type', 'lesson1', 'status', 'created_at']
    list_filter = ['conflict_type', 'status', 'created_at']
    search_fields = ['description']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'lesson1__group', 'lesson2__group', 'teacher__user', 'classroom'
        )

