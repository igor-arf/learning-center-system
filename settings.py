import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-me-in-production')

DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'learning_center',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'learning_center_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'learning_center_project.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'learning_center_db'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'password'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Redis for caching and Celery
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Celery Configuration (for async tasks)
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Moscow'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# CORS settings
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'learning_center': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Custom settings for the learning center
LEARNING_CENTER_SETTINGS = {
    'DEFAULT_LESSON_DURATION': 45,  # minutes
    'DEFAULT_BREAK_DURATION': 15,   # minutes
    'MAX_DAILY_LESSONS_PER_TEACHER': 8,
    'MIN_WEEKLY_LESSONS_PER_TEACHER': 10,
    'PEAK_TIME_START': '13:00',
    'PEAK_TIME_END': '17:00',
    'WORKING_HOURS_START': '11:00',
    'WORKING_HOURS_END': '18:00',
    
    # Email settings for notifications
    'NOTIFICATION_EMAIL': os.environ.get('NOTIFICATION_EMAIL'),
    'SMTP_HOST': os.environ.get('SMTP_HOST', 'localhost'),
    'SMTP_PORT': int(os.environ.get('SMTP_PORT', 587)),
    'SMTP_USER': os.environ.get('SMTP_USER'),
    'SMTP_PASSWORD': os.environ.get('SMTP_PASSWORD'),
    
    # SMS settings (if needed)
    'SMS_PROVIDER_API_KEY': os.environ.get('SMS_API_KEY'),
    'SMS_PROVIDER_URL': os.environ.get('SMS_PROVIDER_URL'),
}

# Email configuration
if LEARNING_CENTER_SETTINGS['SMTP_USER']:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = LEARNING_CENTER_SETTINGS['SMTP_HOST']
    EMAIL_PORT = LEARNING_CENTER_SETTINGS['SMTP_PORT']
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = LEARNING_CENTER_SETTINGS['SMTP_USER']
    EMAIL_HOST_PASSWORD = LEARNING_CENTER_SETTINGS['SMTP_PASSWORD']
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# learning_center_project/urls.py
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('learning_center.urls')),
    path('api-auth/', include('rest_framework.urls')),
    
    # React frontend routes - все остальные маршруты направляем на React
    re_path(r'^(?!api|admin|static|media).*, TemplateView.as_view(template_name='index.html')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


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


# requirements.txt
Django==4.2.7
djangorestframework==3.14.0
django-cors-headers==4.3.1
django-filter==23.3
django-redis==5.4.0
psycopg2-binary==2.9.9
celery==5.3.4
redis==5.0.1
whitenoise==6.6.0
gunicorn==21.2.0
python-dotenv==1.0.0

# Дополнительные пакеты для разработки
pytest==7.4.3
pytest-django==4.7.0
factory-boy==3.3.0
coverage==7.3.2
black==23.11.0
flake8==6.1.0


# package.json (для React frontend)
{
  "name": "learning-center-frontend",
  "version": "1.0.0",
  "description": "Frontend for Learning Center Management System",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint . --ext .js,.jsx,.ts,.tsx",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "next": "^14.0.0",
    "typescript": "^5.2.2",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "tailwindcss": "^3.3.5",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.31",
    "lucide-react": "^0.292.0",
    "axios": "^1.6.0",
    "date-fns": "^2.30.0",
    "@headlessui/react": "^1.7.17",
    "react-hook-form": "^7.47.0",
    "react-query": "^3.39.3",
    "recharts": "^2.8.0"
  },
  "devDependencies": {
    "eslint": "^8.53.0",
    "eslint-config-next": "^14.0.0",
    "@typescript-eslint/eslint-plugin": "^6.11.0",
    "@typescript-eslint/parser": "^6.11.0",
    "prettier": "^3.0.3",
    "prettier-plugin-tailwindcss": "^0.5.7"
  }
}


# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: learning_center_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DEBUG=True
      - DB_HOST=db
      - REDIS_URL=redis://redis:6379/0

  celery:
    build: .
    command: celery -A learning_center_project worker -l info
    volumes:
      - .:/app
    depends_on:
      - db
      - redis
    environment:
      - DEBUG=True
      - DB_HOST=db
      - REDIS_URL=redis://redis:6379/0

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development

volumes:
  postgres_data:


# Dockerfile (для Django backend)
FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "learning_center_project.wsgi:application"]


# .env.example
# Django settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=learning_center_db
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Email settings (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# SMS settings (optional)
SMS_API_KEY=your-sms-api-key
SMS_PROVIDER_URL=https://api.sms-provider.com/send

# Notification email
NOTIFICATION_EMAIL=admin@learningcenter.com