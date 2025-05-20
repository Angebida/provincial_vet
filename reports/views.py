from django.views.generic import TemplateView, ListView
from django.db.models import Sum, Count, F, Q, When, Case
from django.utils import timezone
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import models
from django.core.cache import cache
from itertools import chain  # Add this import at the top
from vet_supplies.models import VeterinarySupply, VeterinarySupplyRequest
from office_supplies.models import OfficeSupply, OfficeSupplyRequest
from .models import InventoryMovement
import csv
from django.db.models.functions import TruncDate
from datetime import timedelta
from django.core.serializers.json import DjangoJSONEncoder
import json

class DashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'reports/dashboard.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        # Enhanced analytics
        analytics = self.get_analytics_data()
        context.update(analytics)
        
        # Get recent movements with caching
        context['movements'] = self.get_cached_movements()
        
        # Filter supplies
        filter_data = self.get_filtered_supplies(self.request.GET.get('filter', ''))
        context.update(filter_data)
        
        return context

    def get_analytics_data(self):
        """Get consolidated analytics data"""
        today = timezone.now().date()
        analytics = {}

        # Stock status with percentage calculations
        stock_stats = self.get_stock_status()
        total_items = sum(sum(category.values()) for category in stock_stats.values())
        
        analytics['stock_status'] = stock_stats
        analytics['total_supplies'] = total_items
        analytics['stock_percentages'] = {
            level: {
                'vet': (stats['vet'] / total_items * 100) if total_items > 0 else 0,
                'office': (stats['office'] / total_items * 100) if total_items > 0 else 0
            }
            for level, stats in stock_stats.items()
        }

        # Extended expiring items data
        expiring = self.get_expiring_data(today)
        analytics['expiring_soon_count'] = expiring['counts']
        analytics['expiring_soon_percent'] = expiring['percentage']
        analytics['expiring_items'] = expiring['items']

        # Enhanced pending requests data
        pending = self.get_pending_data()
        analytics['pending_requests'] = pending['counts']
        analytics['pending_items'] = pending['items']
        analytics['pending_total'] = pending['total_requests']  # Changed from pending_value to pending_total

        # Activity trends
        activity = self.get_activity_trends()
        analytics['chart_data'] = activity['trends']
        analytics['type_chart_data'] = activity['distribution']
        analytics['activity_stats'] = activity['stats']

        # Add supply trend data
        analytics['supply_trends'] = self.get_supply_trends()
        
        return analytics

    def get_expiring_data(self, today):
        """Get detailed expiring items data"""
        thirty_days = today + timezone.timedelta(days=30)
        
        vet_expiring = VeterinarySupply.objects.filter(
            expiration_date__gt=today,
            expiration_date__lte=thirty_days
        )
        office_expiring = OfficeSupply.objects.filter(
            expiration_date__gt=today,
            expiration_date__lte=thirty_days
        )

        total_items = VeterinarySupply.objects.count() + OfficeSupply.objects.count()
        total_expiring = vet_expiring.count() + office_expiring.count()
        
        return {
            'counts': {
                'vet': vet_expiring.count(),
                'office': office_expiring.count()
            },
            'percentage': (total_expiring / total_items * 100) if total_items > 0 else 0,
            'items': {
                'vet': vet_expiring.values('name', 'expiration_date', 'quantity')[:5],
                'office': office_expiring.values('name', 'expiration_date', 'quantity')[:5]
            }
        }

    def get_pending_data(self):
        """Get enhanced pending requests data"""
        vet_pending = VeterinarySupplyRequest.objects.filter(status='pending')
        office_pending = OfficeSupplyRequest.objects.filter(status='pending')

        return {
            'counts': {
                'vet': vet_pending.count(),
                'office': office_pending.count()
            },
            'items': {
                'vet': vet_pending.select_related('supply', 'requester')[:5],
                'office': office_pending.select_related('supply', 'requester')[:5]
            },
            # Remove total_value calculation since price field doesn't exist
            'total_requests': {
                'vet': vet_pending.aggregate(
                    total=Count('id')
                )['total'] or 0,
                'office': office_pending.aggregate(
                    total=Count('id')
                )['total'] or 0
            }
        }

    def get_activity_trends(self):
        """Get activity trends for charts"""
        today = timezone.now().date()
        last_30_days = today - timezone.timedelta(days=30)
        
        movements = InventoryMovement.objects.filter(
            timestamp__date__gte=last_30_days
        ).annotate(
            date=TruncDate('timestamp')
        ).values('date').annotate(
            created=Count('id', filter=Q(action='created')),
            restocked=Count('id', filter=Q(action='restocked')),
            depleted=Count('id', filter=Q(action='depleted')),
            approved=Count('id', filter=Q(action='request_approved'))
        ).order_by('date')

        # Calculate stats
        today_movements = InventoryMovement.objects.filter(
            timestamp__date=today
        )
        most_active_items = InventoryMovement.objects.values(
            'item_name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]

        activity_stats = {
            'total_movements': InventoryMovement.objects.count(),
            'today_movements': today_movements.count(),
            'most_active_items': list(most_active_items)
        }

        dates = []
        created_data = []
        restocked_data = []
        depleted_data = []
        approved_data = []

        current_date = last_30_days
        while current_date <= today:
            dates.append(current_date.strftime('%Y-%m-%d'))
            movement = next(
                (m for m in movements if m['date'] == current_date),
                {'created': 0, 'restocked': 0, 'depleted': 0, 'approved': 0}
            )
            
            created_data.append(movement['created'])
            restocked_data.append(movement['restocked'])
            depleted_data.append(movement['depleted'])
            approved_data.append(movement['approved'])
            
            current_date += timezone.timedelta(days=1)

        return {
            'trends': {
                'dates': dates,
                'series': [
                    {'name': 'New Items', 'data': created_data},
                    {'name': 'Restocked', 'data': restocked_data},
                    {'name': 'Depleted', 'data': depleted_data},
                    {'name': 'Approved Requests', 'data': approved_data}
                ]
            },
            'distribution': self.get_type_distribution(),
            'stats': activity_stats  # Add stats to the returned dictionary
        }

    def get_type_distribution(self):
        """Get supply type distribution data with percentages"""
        vet_count = VeterinarySupply.objects.count()
        office_count = OfficeSupply.objects.count()
        total = vet_count + office_count
        
        # Calculate percentages
        vet_percent = round((vet_count / total * 100), 1) if total > 0 else 0
        office_percent = round((office_count / total * 100), 1) if total > 0 else 0
        
        return {
            'labels': [f'Veterinary ({vet_percent}%)', f'Office ({office_percent}%)'],
            'series': [vet_count, office_count]
        }

    def get_stock_status(self):
        return {
            'low': {
                'vet': VeterinarySupply.objects.filter(quantity__lte=F('reorder_level')).count(),
                'office': OfficeSupply.objects.filter(quantity__lte=F('reorder_level')).count()
            },
            'warning': {
                'vet': VeterinarySupply.objects.filter(
                    quantity__gt=F('reorder_level'),
                    quantity__lte=F('minimum_stock')
                ).count(),
                'office': OfficeSupply.objects.filter(
                    quantity__gt=F('reorder_level'),
                    quantity__lte=F('minimum_stock')
                ).count()
            },
            'adequate': {
                'vet': VeterinarySupply.objects.filter(
                    quantity__gt=F('minimum_stock')
                ).count(),
                'office': OfficeSupply.objects.filter(
                    quantity__gt=F('minimum_stock')
                ).count()
            }
        }

    def get_low_stock_counts(self):
        return {
            'vet': VeterinarySupply.objects.filter(quantity__lte=F('reorder_level')).count(),
            'office': OfficeSupply.objects.filter(quantity__lte=F('reorder_level')).count()
        }

    def get_filtered_supplies(self, filter_type):
        """Get filtered supplies with proper type annotation"""
        # Query veterinary supplies based on filter
        vet_supplies = VeterinarySupply.objects.select_related('category', 'unit')
        office_supplies = OfficeSupply.objects.select_related('category', 'unit')

        today = timezone.now().date()
        thirty_days = today + timezone.timedelta(days=30)

        # Apply filters
        if filter_type == 'low':
            vet_supplies = vet_supplies.filter(quantity__lte=F('reorder_level'))
            office_supplies = office_supplies.filter(quantity__lte=F('reorder_level'))
        elif filter_type == 'warning':
            vet_supplies = vet_supplies.filter(
                quantity__gt=F('reorder_level'),
                quantity__lte=F('minimum_stock')
            )
            office_supplies = office_supplies.filter(
                quantity__gt=F('reorder_level'),
                quantity__lte=F('minimum_stock')
            )
        elif filter_type == 'adequate':
            vet_supplies = vet_supplies.filter(quantity__gt=F('minimum_stock'))
            office_supplies = office_supplies.filter(quantity__gt=F('minimum_stock'))
        elif filter_type == 'expiring':
            vet_supplies = vet_supplies.filter(
                expiration_date__gt=today,
                expiration_date__lte=thirty_days
            )
            office_supplies = office_supplies.filter(
                expiration_date__gt=today,
                expiration_date__lte=thirty_days
            )

        # Convert to list and add type attribute
        vet_list = list(vet_supplies)
        office_list = list(office_supplies)
        
        for supply in vet_list:
            supply.type = 'vet'
        for supply in office_list:
            supply.type = 'office'

        return {
            'filtered_supplies': vet_list + office_list,
            'vet_supplies': vet_list,
            'office_supplies': office_list,
            'current_filter': filter_type
        }

    def get_cached_movements(self):
        """Get recent movements with caching"""
        cache_key = 'recent_inventory_movements'
        movements = cache.get(cache_key)
        
        if not movements:
            movements = list(InventoryMovement.objects.select_related(
                'content_type'
            ).order_by('-timestamp')[:10])
            cache.set(cache_key, movements, timeout=60*5)  # Cache for 5 minutes
        
        return movements

    def get_supply_trends(self):
        """Get supply trends for the chart"""
        today = timezone.now().date()
        start_date = today - timezone.timedelta(days=30)
        
        vet_supplies = VeterinarySupply.objects.filter(
            created_at__date__gte=start_date
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id'),
            total_quantity=Sum('quantity')
        ).order_by('date')

        office_supplies = OfficeSupply.objects.filter(
            created_at__date__gte=start_date
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id'),
            total_quantity=Sum('quantity')
        ).order_by('date')
        
        dates = []
        vet_data = []
        office_data = []
        total_data = []
        
        current_date = start_date
        while current_date <= today:
            dates.append(current_date.strftime('%Y-%m-%d'))
            
            vet_record = next(
                (x for x in vet_supplies if x['date'] == current_date),
                {'total_quantity': 0}
            )
            office_record = next(
                (x for x in office_supplies if x['date'] == current_date),
                {'total_quantity': 0}
            )
            
            vet_data.append(vet_record['total_quantity'])
            office_data.append(office_record['total_quantity'])
            total_data.append(vet_record['total_quantity'] + office_record['total_quantity'])
            
            current_date += timezone.timedelta(days=1)
        
        return {
            'dates': dates,
            'series': [
                {'name': 'Total Supplies', 'data': total_data},
                {'name': 'Veterinary', 'data': vet_data},
                {'name': 'Office', 'data': office_data}
            ]
        }

class InventoryMovementListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = InventoryMovement
    template_name = 'reports/movements.html'
    context_object_name = 'movements'
    paginate_by = 50

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        queryset = InventoryMovement.objects.all()
        
        # Date range filter
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(
                timestamp__date__range=[start_date, end_date]
            )
        
        # Type filter
        item_type = self.request.GET.get('type')
        if item_type:
            queryset = queryset.filter(item_type=item_type)

        # Action filter
        action = self.request.GET.get('action')
        if action:
            queryset = queryset.filter(action=action)

        return queryset.order_by('-timestamp')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get counts for badges
        context['type_counts'] = {
            'vet': InventoryMovement.objects.filter(item_type='vet').count(),
            'office': InventoryMovement.objects.filter(item_type='office').count()
        }
        
        context['action_counts'] = {
            action: InventoryMovement.objects.filter(action=action).count()
            for action, _ in self.get_actions()
        }
        
        context['actions'] = self.get_actions()
        return context
        
    def get_actions(self):
        return [
            ('created', 'Added Items'),
            ('restocked', 'Restocked Items'),
            ('depleted', 'Depleted Items'),
            ('request_approved', 'Approved Requests'),
            ('deleted', 'Deleted Items')
        ]

def export_report(request):
    if not request.user.is_staff:
        return HttpResponse('Unauthorized', status=401)

    # Get all filter parameters
    report_type = request.GET.get('type', 'all')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    stock_status = request.GET.get('stock_status')
    category = request.GET.get('category')
    expiration = request.GET.get('expiration')
    
    response = HttpResponse(content_type='text/csv')
    filename = f"inventory_{report_type}_{timezone.now().strftime('%Y%m%d_%H%M')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(['Name', 'Category', 'Quantity', 'Unit', 'Status', 'Expiration Date', 'Notes'])
    
    # Get queryset based on type
    if report_type == 'vet':
        queryset = VeterinarySupply.objects.select_related('category', 'unit')
    elif report_type == 'office':
        queryset = OfficeSupply.objects.select_related('category', 'unit')
    else:
        # Handle combined query
        vet_qs = VeterinarySupply.objects.select_related('category', 'unit')
        office_qs = OfficeSupply.objects.select_related('category', 'unit')
        queryset = list(chain(vet_qs, office_qs))  # Convert chain to list immediately

    # Apply filters only for non-chained querysets
    if not isinstance(queryset, list):  # Changed from chain to list
        today = timezone.now().date()
        
        if stock_status == 'low':
            queryset = queryset.filter(quantity__lte=F('reorder_level'), quantity__gt=0)
        elif stock_status == 'out':
            queryset = queryset.filter(quantity=0)
        elif stock_status == 'adequate':
            queryset = queryset.filter(quantity__gt=F('reorder_level'))

        if category:
            queryset = queryset.filter(category_id=category)

        if expiration == 'expired':
            queryset = queryset.filter(expiration_date__lt=today)
        elif expiration == 'expiring-soon':
            queryset = queryset.filter(
                expiration_date__gte=today,
                expiration_date__lte=today + timezone.timedelta(days=30)
            )
        elif expiration == 'valid':
            queryset = queryset.filter(expiration_date__gt=today + timezone.timedelta(days=30))

    # Write data to CSV
    for item in queryset:
        writer.writerow([
            item.name,
            item.category.name,
            item.quantity,
            item.unit.display_name,
            item.stock_status.title(),
            item.expiration_date.strftime('%Y-%m-%d') if item.expiration_date else 'N/A',
            item.notes or ''
        ])
    
    return response