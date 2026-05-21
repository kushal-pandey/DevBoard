from rest_framework import serializers
from .models import Project, ProjectMember, Sprint
from apps.accounts.serializers import UserSerializer


class ProjectMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ProjectMember
        fields = ['id', 'user', 'role', 'joined_at']


class ProjectSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()
    issue_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'key', 'description', 'status',
            'owner', 'member_count', 'issue_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def get_member_count(self, obj):
        return obj.members.count()

    def get_issue_count(self, obj):
        return obj.issues.count()

    def create(self, validated_data):
        project = Project.objects.create(owner=self.context['request'].user, **validated_data)
        ProjectMember.objects.create(
            project=project,
            user=self.context['request'].user,
            role=ProjectMember.Role.ADMIN
        )
        return project


class SprintSerializer(serializers.ModelSerializer):
    issue_count = serializers.SerializerMethodField()

    class Meta:
        model = Sprint
        fields = ['id', 'project', 'name', 'goal', 'status', 'start_date', 'end_date', 'issue_count', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_issue_count(self, obj):
        return obj.issues.count()