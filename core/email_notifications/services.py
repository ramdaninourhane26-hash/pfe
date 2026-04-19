from .tasks import send_email_task

def send_notification_email(user, message):
    send_email_task.delay(
        user.email,
        "Notification 🔔",
        message
    )
    from notifications.models import Notification
from notifications.models import Notification
from email_notifications.services import send_notification_email

def notify_all(user, message):
    Notification.objects.create(user=user, message=message)
    send_notification_email(user, message)
 