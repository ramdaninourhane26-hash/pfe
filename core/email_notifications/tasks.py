from celery import shared_task
from django.core.mail import send_mail
from .models import EmailLog
@shared_task
def send_email_task(email, subject, message):
    from .models import EmailLog  
    send_mail(
        subject,
        message,
        'your_email@gmail.com',
        [email],
        fail_silently=False,
    )

    EmailLog.objects.create(
        email=email,
        subject=subject,
        message=message
    )

    