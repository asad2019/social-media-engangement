import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'engagement_platform.settings')

app = Celery('engagement_platform')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'daily-reconciliation': {
        'task': 'wallets.tasks.daily_reconciliation',
        'schedule': 60.0 * 60.0 * 24.0,  # Every 24 hours
    },
    'update-platform-metrics': {
        'task': 'admin_console.tasks.update_platform_metrics',
        'schedule': 60.0 * 60.0 * 24.0,  # Every 24 hours
    },
    'cleanup-expired-jobs': {
        'task': 'jobs.tasks.cleanup_expired_jobs',
        'schedule': 60.0 * 60.0,  # Every hour
    },
    'process-pending-withdrawals': {
        'task': 'wallets.tasks.process_pending_withdrawals',
        'schedule': 60.0 * 30.0,  # Every 30 minutes
    },
    'verify-pending-jobs': {
        'task': 'verification.tasks.process_verification_queue',
        'schedule': 60.0 * 5.0,  # Every 5 minutes
    },
    'update-account-scores': {
        'task': 'users.tasks.update_account_scores',
        'schedule': 60.0 * 60.0 * 6.0,  # Every 6 hours
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
