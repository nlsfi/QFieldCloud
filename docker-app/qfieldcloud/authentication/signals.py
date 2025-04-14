import logging

from auditlog.models import LogEntry
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now

logger = logging.getLogger("auditlog")


# Listen post save of LogEntry, which is created after a successfull auditlog entry
@receiver(post_save, sender=LogEntry)
def log_audit_entry_to_file(sender, instance, created, **kwargs):
    if created:
        logger.info(
            f"{instance.timestamp} | Action: {instance.get_action_display()} | "
            f"User: {instance.actor} | Model: {instance.content_type} | Object ID: {instance.object_pk}"
        )


@receiver(user_logged_in)
def log_all_logins(sender, request, user, **kwargs):
    logger.info(
        f"[{now()}] Successful login by user '{user.username}' from IP {get_client_ip(request)}"
    )


def get_client_ip(request):
    if x_forwarded_for := request.headers.get("x-forwarded-for"):
        return x_forwarded_for

    return request.META.get("REMOTE_ADDR")
