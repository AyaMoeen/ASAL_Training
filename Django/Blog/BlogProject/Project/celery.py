from __future__ import absolute_import, unicode_literals
import os
from celery import Celery # type: ignore
from django.conf import settings
from celery.schedules import crontab # type: ignore

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings')

app = Celery('Project')
app.conf.beat_schedule = {
    'fetch-data-every-3-hours': {
        'task': 'Blog.tasks.fetch_all_data',
        'schedule': crontab(minute=0, hour='*/3'),
        'args': (),
    },
}
app.conf.enable_utc = False
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
