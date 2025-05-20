from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from vet_supplies.models import VeterinarySupply, VeterinarySupplyRequest
from office_supplies.models import OfficeSupply, OfficeSupplyRequest
from .models import InventoryMovement

@receiver(pre_save, sender=VeterinarySupply)
@receiver(pre_save, sender=OfficeSupply)
def store_original_state(sender, instance, **kwargs):
    if instance.pk:  # Only for existing objects
        try:
            original = sender.objects.get(pk=instance.pk)
            instance._original_quantity = original.quantity
            instance._original_state = {
                'name': original.name,
                'category': original.category,
                'unit': original.unit,
                'notes': original.notes,
                'expiration_date': original.expiration_date if hasattr(original, 'expiration_date') else None
            }
        except sender.DoesNotExist:
            instance._original_quantity = None
            instance._original_state = None

@receiver(post_save, sender=VeterinarySupply)
@receiver(post_save, sender=OfficeSupply)
def log_supply_changes(sender, instance, created, **kwargs):
    content_type = ContentType.objects.get_for_model(instance)
    
    if created:
        action = 'created'
    else:
        # Check for changes
        if hasattr(instance, '_original_quantity') and instance._original_quantity != instance.quantity:
            action = 'restocked' if instance.quantity > instance._original_quantity else 'depleted'
        elif hasattr(instance, '_original_state') and any(
            getattr(instance, field) != value 
            for field, value in instance._original_state.items()
        ):
            action = 'updated'
        else:
            return  # No changes detected
            
    InventoryMovement.objects.create(
        content_type=content_type,
        object_id=instance.id,
        action=action,
        quantity=instance.quantity,
        previous_quantity=getattr(instance, '_original_quantity', 0),
        item_type='vet' if isinstance(instance, VeterinarySupply) else 'office',
        item_name=instance.name,
        category=instance.category.name,
        unit=instance.unit
    )

@receiver(post_save, sender=VeterinarySupplyRequest)
@receiver(post_save, sender=OfficeSupplyRequest)
def log_request_changes(sender, instance, created, **kwargs):
    if not created and instance.status in ['approved', 'rejected']:
        content_type = ContentType.objects.get_for_model(instance.supply)
        InventoryMovement.objects.create(
            content_type=content_type,
            object_id=instance.supply.id,
            action=f'request_{instance.status}',
            quantity=instance.quantity,
            previous_quantity=instance.supply.quantity,
            item_type='veterinarysupply' if isinstance(instance.supply, VeterinarySupply) else 'officesupply',
            item_name=instance.supply.name,
            category=instance.supply.category.name,
            unit=instance.supply.unit
        )

@receiver(post_delete, sender=VeterinarySupply)
@receiver(post_delete, sender=OfficeSupply)
def log_delete(sender, instance, **kwargs):
    content_type = ContentType.objects.get_for_model(instance)
    InventoryMovement.objects.create(
        content_type=content_type,
        object_id=instance.id,
        action='deleted',
        quantity=0,
        previous_quantity=instance.quantity,
        item_type='veterinarysupply' if isinstance(instance, VeterinarySupply) else 'officesupply',
        item_name=instance.name,
        category=instance.category.name,
        unit=instance.unit
    )