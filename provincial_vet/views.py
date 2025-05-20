from django.shortcuts import render
from django.db.models import Count, F
from office_supplies.models import OfficeSupply, OfficeSupplyRequest
from vet_supplies.models import VeterinarySupply, VeterinarySupplyRequest

def home_view(request):
    context = {}
    
    if request.user.is_authenticated:
        # Vet supplies stats
        context['vet_total_items'] = VeterinarySupply.objects.count()
        context['vet_low_stock'] = VeterinarySupply.objects.filter(
            quantity__lte=F('minimum_stock')
        ).count()
        context['pending_vet_count'] = VeterinarySupplyRequest.objects.filter(
            status='pending'
        ).count()
        
        # Office supplies stats
        context['office_total_items'] = OfficeSupply.objects.count()
        context['office_reorder_count'] = OfficeSupply.objects.filter(
            quantity__lte=F('reorder_level')
        ).count()
        context['pending_office_count'] = OfficeSupplyRequest.objects.filter(
            status='pending'
        ).count()
    
    return render(request, 'home.html', context)
