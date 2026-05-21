from rest_framework import serializers
from .models import Issue, Comment, Label
from apps.accounts.serializers import UserSerializer


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ['id', 'name', 'color', 'project']
        read_only_fields = ['id']


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'issue', 'author', 'body', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

    def create(self, validated_data):
        return Comment.objects.create(author=self.context['request'].user, **validated_data)


class IssueSerializer(serializers.ModelSerializer):
    reporter = UserSerializer(read_only=True)
    assignee = UserSerializer(read_only=True)
    assignee_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    labels = LabelSerializer(many=True, read_only=True)
    label_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Issue
        fields = [
            'id', 'project', 'sprint', 'title', 'description',
            'status', 'priority', 'issue_type',
            'reporter', 'assignee', 'assignee_id',
            'labels', 'label_ids',
            'story_points', 'due_date',
            'comment_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'reporter', 'created_at', 'updated_at']

    def get_comment_count(self, obj):
        return obj.comments.count()

    def create(self, validated_data):
        assignee_id = validated_data.pop('assignee_id', None)
        label_ids = validated_data.pop('label_ids', [])
        issue = Issue.objects.create(
            reporter=self.context['request'].user,
            assignee_id=assignee_id,
            **validated_data
        )
        if label_ids:
            issue.labels.set(label_ids)
        return issue

    def update(self, instance, validated_data):
        assignee_id = validated_data.pop('assignee_id', None)
        label_ids = validated_data.pop('label_ids', None)
        if assignee_id is not None:
            instance.assignee_id = assignee_id
        if label_ids is not None:
            instance.labels.set(label_ids)
        return super().update(instance, validated_data)