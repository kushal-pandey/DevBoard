from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IssueViewSet, LabelViewSet

router = DefaultRouter()
router.register(r'labels', LabelViewSet, basename='label')
router.register(r'', IssueViewSet, basename='issue')

urlpatterns = [
    path('', include(router.urls)),
]