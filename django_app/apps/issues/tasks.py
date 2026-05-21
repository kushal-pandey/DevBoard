from celery import shared_task


@shared_task
def send_issue_assignment_email(issue_id):
    """Send email when an issue is assigned to someone."""
    from .models import Issue
    try:
        issue = Issue.objects.select_related('assignee', 'reporter', 'project').get(id=issue_id)
        if not issue.assignee or not issue.assignee.email:
            return

        from django.core.mail import send_mail
        send_mail(
            subject=f'[{issue.project.key}] Issue Assigned to You: {issue.title}',
            message=(
                f'Hi {issue.assignee.first_name or issue.assignee.username},\n\n'
                f'You have been assigned a new issue on DevBoard.\n\n'
                f'Project : {issue.project.name}\n'
                f'Issue   : {issue.title}\n'
                f'Priority: {issue.get_priority_display()}\n'
                f'Type    : {issue.get_issue_type_display()}\n'
                f'Reporter: {issue.reporter.email}\n\n'
                f'Log in to DevBoard to view and update this issue.\n\n'
                f'— DevBoard Team'
            ),
            from_email='DevBoard <noreply@devboard.com>',
            recipient_list=[issue.assignee.email],
            fail_silently=True,
        )
    except Issue.DoesNotExist:
        pass


@shared_task
def generate_sprint_report(sprint_id):
    """Generate a sprint completion report."""
    from apps.projects.models import Sprint
    from .models import Issue
    try:
        sprint = Sprint.objects.select_related('project').get(id=sprint_id)
        issues = Issue.objects.filter(sprint=sprint)
        total = issues.count()
        done = issues.filter(status=Issue.Status.DONE).count()
        completion_rate = round((done / total * 100), 2) if total > 0 else 0

        report = {
            'sprint': sprint.name,
            'project': sprint.project.name,
            'total_issues': total,
            'completed': done,
            'completion_rate': f'{completion_rate}%',
        }
        print(f'Sprint Report Generated: {report}')
        return report
    except Sprint.DoesNotExist:
        return None