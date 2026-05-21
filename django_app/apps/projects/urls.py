from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, SprintViewSet

router = DefaultRouter()
router.register(r'', ProjectViewSet, basename='project')
router.register(r'sprints', SprintViewSet, basename='sprint')

urlpatterns = [
    path('', include(router.urls)),
]