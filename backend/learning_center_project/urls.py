# learning_center/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from learning_center.views import *

router = DefaultRouter()
router.register(r"branches", BranchViewSet)
router.register(r"teachers", TeacherViewSet)
router.register(r"students", StudentViewSet)
router.register(r"groups", GroupViewSet)
router.register(r"schedule", ScheduleViewSet, basename="schedule")

urlpatterns = [
    path("api/", include(router.urls)),
]
