import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ganasaksaak.settings')

app = Celery('ganasaksaak')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'verificar-pagos-cada-10-minutos': {
        'task': 'apps.sorteo.tasks.schedule_pending_payment_checks', 
        'schedule': crontab(minute='*/5'),
    },
}
