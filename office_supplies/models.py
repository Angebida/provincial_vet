from django.db import models
from users.models import CustomUser
from django.utils import timezone
from inventory.models import UnitMeasure

class OfficeSupplyCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class OfficeSupply(models.Model):
    UNIT_CHOICES = [
        ('units', 'Units'),
        ('reams', 'Reams'),
        ('boxes', 'Boxes'),
        ('pcs', 'Pieces'),
        ('sets', 'Sets'),
        ('packs', 'Packs'),
        ('rolls', 'Rolls'),
        ('cartridges', 'Cartridges'),
        ('bottles', 'Bottles')
    ]

    name = models.CharField(max_length=255)
    category = models.ForeignKey(OfficeSupplyCategory, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    expiration_date = models.DateField(null=True, blank=True)
    unit = models.ForeignKey(
        UnitMeasure,
        on_delete=models.PROTECT,
        related_name='office_supplies'
    )
    minimum_stock = models.PositiveIntegerField(default=10)
    reorder_level = models.PositiveIntegerField(default=5, verbose_name='Low Stock Level')
    last_ordered = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_quantity = self.quantity if self.pk else None

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields', None)
        if update_fields is None or 'quantity' in update_fields:
            self._original_quantity = OfficeSupply.objects.get(pk=self.pk).quantity if self.pk else None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.category})"

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

    @property
    def stock_status(self):
        if self.quantity == 0:
            return 'out'
        elif self.quantity <= self.reorder_level:
            return 'low'
        elif self.quantity <= self.minimum_stock:
            return 'warning'
        return 'adequate'

class OfficeSupplyRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]

    supply = models.ForeignKey(OfficeSupply, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requester = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='office_requests')
    approved_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True, 
        related_name='office_approvals'
    )
    purpose = models.TextField(blank=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    is_bulk = models.BooleanField(default=False, verbose_name='Bulk Request')

    def __str__(self):
        return f"Request #{self.id} - {self.supply.name}"

class RequestItem(models.Model):
    request = models.ForeignKey(OfficeSupplyRequest, on_delete=models.CASCADE, related_name='items')
    supply = models.ForeignKey(OfficeSupply, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.supply.name} - {self.quantity} {self.supply.unit}"