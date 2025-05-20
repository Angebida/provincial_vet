from django.db import models
from users.models import CustomUser
from django.utils import timezone
from inventory.models import UnitMeasure

class VeterinarySupplyCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class VeterinarySupply(models.Model):
    UNIT_CHOICES = [
        ('units', 'Units'),
        ('boxes', 'Boxes'),
        ('bottles', 'Bottles'),
        ('vials', 'Vials'),
        ('sachets', 'Sachets'),
        ('pcs', 'Pieces'),
        ('tablets', 'Tablets'),
        ('ampoules', 'Ampoules'),
        ('doses', 'Doses')
    ]

    name = models.CharField(max_length=255)
    category = models.ForeignKey(VeterinarySupplyCategory, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    unit = models.ForeignKey(
        UnitMeasure,
        on_delete=models.PROTECT,
        related_name='vet_supplies'
    )
    expiration_date = models.DateField(null=True, blank=True)
    last_restocked = models.DateTimeField(default=timezone.now)
    minimum_stock = models.PositiveIntegerField(default=10)
    reorder_level = models.PositiveIntegerField(default=5, verbose_name='Low Stock Level')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_quantity = self.quantity if self.pk else None

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields', None)
        if update_fields is None or 'quantity' in update_fields:
            self._original_quantity = VeterinarySupply.objects.get(pk=self.pk).quantity if self.pk else None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.category})"

    @property
    def stock_status(self):
        if self.quantity == 0:
            return 'out'
        elif self.quantity <= self.reorder_level:
            return 'low'
        return 'adequate'

    @property
    def needs_reorder(self):
        return self.quantity <= self.reorder_level

    @property 
    def expiration_status(self):
        if not self.expiration_date:
            return 'no-date'
        
        today = timezone.now().date()
        days_until_expiry = (self.expiration_date - today).days
        
        if days_until_expiry < 0:
            return 'expired'
        elif days_until_expiry <= 30:
            return 'expiring-soon'
        return 'valid'

class VeterinarySupplyRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]

    requester = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    supply = models.ForeignKey(VeterinarySupply, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    purpose = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True, 
        related_name='vet_approvals'
    )
    approval_date = models.DateTimeField(null=True, blank=True)
    urgency = models.BooleanField(default=False)
    is_bulk = models.BooleanField(default=False, verbose_name='Bulk Request')

    def __str__(self):
        return f"Request #{self.id} - {self.supply.name}"

class RequestItem(models.Model):
    request = models.ForeignKey(VeterinarySupplyRequest, on_delete=models.CASCADE, related_name='items')
    supply = models.ForeignKey(VeterinarySupply, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.supply.name} - {self.quantity} {self.supply.unit}"