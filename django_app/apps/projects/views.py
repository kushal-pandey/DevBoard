from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from .models import Project, ProjectMember, Sprint
from .serializers import ProjectSerializer, ProjectMemberSerializer, SprintSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Project.objects
            .filter(members=self.request.user)
            .select_related('owner')
            .prefetch_related('members')
        )

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        project = self.get_object()
        members = ProjectMember.objects.filter(project=project).select_related('user')
        serializer = ProjectMemberSerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        project = self.get_object()
        user_id = request.data.get('user_id')
        role = request.data.get('role', ProjectMember.Role.DEVELOPER)

        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        member, created = ProjectMember.objects.get_or_create(
            project=project, user=user, defaults={'role': role}
        )
        if not created:
            return Response({'error': 'User is already a member.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ProjectMemberSerializer(member).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='remove_member/(?P<user_id>[^/.]+)')
    def remove_member(self, request, pk=None, user_id=None):
        project = self.get_object()
        ProjectMember.objects.filter(project=project, user_id=user_id).delete()
        return Response({'message': 'Member removed.'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        project = self.get_object()
        cache_key = f'project_stats_{project.id}'
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        from apps.issues.models import Issue
        stats = {
            'total_issues': Issue.objects.filter(project=project).count(),
            'open': Issue.objects.filter(project=project, status=Issue.Status.OPEN).count(),
            'in_progress': Issue.objects.filter(project=project, status=Issue.Status.IN_PROGRESS).count(),
            'in_review': Issue.objects.filter(project=project, status=Issue.Status.IN_REVIEW).count(),
            'done': Issue.objects.filter(project=project, status=Issue.Status.DONE).count(),
            'cancelled': Issue.objects.filter(project=project, status=Issue.Status.CANCELLED).count(),
            'total_members': project.members.count(),
            'total_sprints': project.sprints.count(),
            'active_sprints': project.sprints.filter(status=Sprint.Status.ACTIVE).count(),
        }
        cache.set(cache_key, stats, timeout=300)  # cache for 5 minutes
        return Response(stats)


class SprintViewSet(viewsets.ModelViewSet):
    serializer_class = SprintSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Sprint.objects.filter(
            project__members=self.request.user
        ).select_related('project')