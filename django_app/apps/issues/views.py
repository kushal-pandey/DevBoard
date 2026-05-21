from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Issue, Comment, Label
from .serializers import IssueSerializer, CommentSerializer, LabelSerializer
from .tasks import send_issue_assignment_email


class IssueViewSet(viewsets.ModelViewSet):
    serializer_class = IssueSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'issue_type', 'assignee', 'project', 'sprint']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'priority', 'due_date', 'story_points']

    def get_queryset(self):
        return (
            Issue.objects
            .filter(project__members=self.request.user)
            .select_related('project', 'reporter', 'assignee', 'sprint')
            .prefetch_related('labels', 'comments')
        )

    def perform_update(self, serializer):
        old_instance = self.get_object()
        old_assignee_id = old_instance.assignee_id
        issue = serializer.save()
        # Fire email task only if assignee changed
        if issue.assignee and str(issue.assignee_id) != str(old_assignee_id):
            send_issue_assignment_email.delay(str(issue.id))

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        issue = self.get_object()
        if request.method == 'GET':
            comments = issue.comments.select_related('author').all()
            return Response(CommentSerializer(comments, many=True).data)

        data = {**request.data, 'issue': str(issue.id)}
        serializer = CommentSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LabelViewSet(viewsets.ModelViewSet):
    serializer_class = LabelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Label.objects.filter(project__members=self.request.user)