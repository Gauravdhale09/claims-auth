# utils.py
from django.core.mail import EmailMessage
from django.conf import settings
import threading
import os
from django.utils import timezone

class EmailThread(threading.Thread):
    def __init__(self, subject, message, recipient_list, attachment_path=None,notifcationObj=None):
        self.subject = subject
        self.message = message
        self.recipient_list = recipient_list
        self.attachment_path = attachment_path
        self.notifcationObj = notifcationObj
        threading.Thread.__init__(self)

    def run(self):
        try:
            common_footer = "\n\n---\nThis is a system-generated email. Please do not reply to this message.\n"

            email = EmailMessage(
                subject=self.subject,
                body=f"{self.message}{common_footer}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=self.recipient_list,
            )

            if self.attachment_path and os.path.exists(self.attachment_path):
                email.attach_file(self.attachment_path)

            send_count = email.send(fail_silently=False)
            print(f"✅ Email sent to {self.recipient_list}")
            if send_count and self.notifcationObj:
                self.notifcationObj.is_notification_sent = True
                self.notifcationObj.lateset_notification_on = timezone.now()
                self.notifcationObj.save()
            return send_count, "mail sent successfully"
        except Exception as e:
            print(f"❌ Email failed: {e}")
            return False, e

def send_mail(subject, message, recipients, attachment_path=None, notifcationObj=None):
    if isinstance(recipients, str):
        recipients = [recipients]
    EmailThread(subject, message, recipients, attachment_path, notifcationObj).start()
    return True
