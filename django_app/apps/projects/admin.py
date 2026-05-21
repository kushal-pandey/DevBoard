from django.contrib import admin
from .models import Project, ProjectMember, Sprint


class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 0
    raw_id_fields = ['user']


class SprintInline(admin.TabularInline):
    model = Sprint
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'key', 'status', 'owner', 'created_at']
    search_fields = ['name', 'key']
    list_filter = ['status']
    raw_id_fields = ['owner']
    inlines = [ProjectMemberInline, SprintInline]


@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'project']
    search_fields = ['name']