from django.contrib import admin
from .models import Issue, Comment, Label


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'status', 'priority', 'issue_type', 'assignee', 'created_at']
    search_fields = ['title', 'description']
    list_filter = ['status', 'priority', 'issue_type', 'project']
    raw_id_fields = ['assignee', 'reporter', 'project', 'sprint']
    filter_horizontal = ['labels']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['issue', 'author', 'created_at']
    search_fields = ['body']
    raw_id_fields = ['issue', 'author']


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'project']
    list_filter = ['project']