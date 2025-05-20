from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from vet_supplies.models import VeterinarySupply
from django.conf import settings

class InventoryMovement(models.Model):
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
        ('restocked', 'Restocked'),
        ('depleted', 'Depleted'),
        ('requested', 'Requested'),  # New action type
        ('request_approved', 'Request Approved'),  # New action type
        ('request_rejected', 'Request Rejected')  # New action type
    ]

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    quantity = models.IntegerField()
    previous_quantity = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    item_type = models.CharField(max_length=50)  # 'vet' or 'office'
    item_name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    unit = models.CharField(max_length=20, null=True, blank=True)  # Add unit field

    class Meta:
        ordering = ['-timestamp']

    def get_badge_class(self):
        if self.action == 'created':
            return 'primary'  # Make created items use primary color
        elif self.action == 'restocked':
            return 'success'
        elif self.action == 'depleted':
            return 'warning'
        elif self.action == 'deleted':
            return 'danger'
        elif self.action == 'updated':
            return 'info'
        return 'secondary'

    def get_formatted_change(self):
        if self.previous_quantity is not None:
            return f"{self.previous_quantity} → {self.quantity}"
        return str(self.quantity)

    def get_relative_time(self):
        from django.utils import timezone
        from django.utils.timesince import timesince
        return timesince(self.timestamp, timezone.now())