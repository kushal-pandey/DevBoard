from django.db import models
from django.conf import settings
import uuid


class Label(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#0075CA')
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='labels')

    class Meta:
        db_table = 'labels'
        unique_together = ['name', 'project']

    def __str__(self):
        return self.name


class Issue(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        IN_REVIEW = 'in_review', 'In Review'
        DONE = 'done', 'Done'
        CANCELLED = 'cancelled', 'Cancelled'

    class Priority(models.TextChoices):
        CRITICAL = 'critical', 'Critical'
        HIGH = 'high', 'High'
        MEDIUM = 'medium', 'Medium'
        LOW = 'low', 'Low'

    class IssueType(models.TextChoices):
        BUG = 'bug', 'Bug'
        FEATURE = 'feature', 'Feature'
        TASK = 'task', 'Task'
        IMPROVEMENT = 'improvement', 'Improvement'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='issues')
    sprint = models.ForeignKey(
        'projects.Sprint', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='issues'
    )
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    issue_type = models.CharField(max_length=20, choices=IssueType.choices, default=IssueType.TASK)
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reported_issues'
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_issues'
    )
    labels = models.ManyToManyField(Label, blank=True)
    story_points = models.PositiveIntegerField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'issues'
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.project.key}] {self.title}'


class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'comments'
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.author.email} on [{self.issue.project.key}]'