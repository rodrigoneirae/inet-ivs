import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inet_ivs.settings')

app = Celery('inet_ivs')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
