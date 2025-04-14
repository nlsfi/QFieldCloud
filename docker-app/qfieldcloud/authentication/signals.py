import logging

from auditlog.models import LogEntry
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger("auditlog")


# Listen post save of LogEntry, which is created after a successfull auditlog entry
@receiver(post_save, sender=LogEntry)
def log_audit_entry_to_file(sender, instance, created, **kwargs):
    if created:
        logger.info(
            f"{instance.timestamp} | Action: {instance.get_action_display()} | "
            f"User: {instance.actor} | Model: {instance.content_type} | Object ID: {instance.object_pk}"
        )
