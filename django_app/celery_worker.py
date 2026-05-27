import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('devboard')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.conf.beat_schedule = {
    'keep-services-alive': {
        'task': 'apps.accounts.tasks.ping_services',
        'schedule': crontab(minute='*/10'),  
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')