from .models import Notification
from email_notifications.tasks import send_email_task
from django.contrib.auth.models import User


def create_notification(user, message):
    return Notification.objects.create(
        user=user,
        message=message
    )


def notify_user(user, message, email_subject=None, email_message=None):
    # 🔔 in-app notification
    create_notification(user, message)

    # 📩 email notification (optional)
    if email_subject and email_message:
        send_email_task.delay(
            email_subject,
            email_message,
            user.email
        )
    
def notify_all_users(message):
    users = User.objects.all()

    for user in users:
        create_notification(user, message)