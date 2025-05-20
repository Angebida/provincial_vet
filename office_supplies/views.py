from django.views.generic import ListView, CreateView, UpdateView, DetailView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.db.models import F, Q
from django.shortcuts import redirect
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.utils import timezone
from .models import OfficeSupply, OfficeSupplyRequest, OfficeSupplyCategory, RequestItem
from .forms import (
    OfficeSupplyForm, RequestForm, BulkSupplyUploadForm,
    RequestItemFormSet, BulkRequestForm  # Add this import
)
from reports.models import InventoryMovement  # Add this import
from inventory.models import UnitMeasure  # Add this import
import csv
import io

class SupplyListView(LoginRequiredMixin, ListView):
    model = OfficeSupply
    template_name = 'office_supplies/list.html'
    context_object_name = 'supplies'
    paginate_by = 10  # Set pagination size

    def get_queryset(self):
        queryset = OfficeSupply.objects.select_related('category').order_by('name')
        
        # Add search query and filters
        stock_status = self.request.GET.get('stock_status')
        if stock_status == 'low':
            queryset = queryset.filter(quantity__lte=F('reorder_level'), quantity__gt=0)
        elif stock_status == 'out':
            queryset = queryset.filter(quantity=0)
        elif stock_status == 'adequate':
            queryset = queryset.filter(quantity__gt=F('reorder_level'))

        # Category filter
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Expiration filter
        expiration = self.request.GET.get('expiration')
        today = timezone.now().date()
        if expiration == 'expired':
            queryset = queryset.filter(expiration_date__lt=today)
        elif expiration == 'expiring-soon':
            queryset = queryset.filter(
                expiration_date__gte=today,
                expiration_date__lte=today + timezone.timedelta(days=30)
            )
        elif expiration == 'valid':
            queryset = queryset.filter(expiration_date__gt=today + timezone.timedelta(days=30))
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = OfficeSupplyCategory.objects.all().order_by('name')
        context['search'] = self.request.GET.get('search', '')
        context['category'] = self.request.GET.get('category', '')
        today = timezone.now().date()
        context['low_stock_count'] = OfficeSupply.objects.filter(
            quantity__lte=F('reorder_level'),
            quantity__gt=0
        ).count()
        context['expiring_count'] = OfficeSupply.objects.filter(
            expiration_date__gt=today,
            expiration_date__lte=today + timezone.timedelta(days=90)  # Extended window
        ).count()
        context['units'] = UnitMeasure.objects.filter(is_active=True)
        
        # Add out of stock count
        context['out_of_stock_count'] = OfficeSupply.objects.filter(
            quantity=0
        ).count()
        
        # Add expired count
        context['expired_count'] = OfficeSupply.objects.filter(
            expiration_date__lt=today
        ).count()
        
        return context

class SupplyCreateView(LoginRequiredMixin, CreateView):
    model = OfficeSupply
    form_class = OfficeSupplyForm
    template_name = 'office_supplies/form.html'
    success_url = '/office-supplies/'  # Updated to match vet pattern

    def form_valid(self, form):
        response = super().form_valid(form)
        # Log the initial creation with initial stock
        if (form.cleaned_data['quantity'] > 0):
            InventoryMovement.objects.create(
                content_type=ContentType.objects.get_for_model(self.object),
                object_id=self.object.id,
                action='created',
                quantity=self.object.quantity,
                previous_quantity=0,
                item_type='office',
                item_name=self.object.name,
                category=self.object.category.name,
                unit=self.object.unit
            )
        messages.success(self.request, f'Supply "{form.instance.name}" has been created.')
        return response

class RequestCreateView(LoginRequiredMixin, CreateView):
    model = OfficeSupplyRequest
    template_name = 'office_supplies/request_form.html'  # Updated path
    form_class = BulkRequestForm
    success_url = reverse_lazy('office-request-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Remove instance since BulkRequestForm is not a ModelForm
        kwargs.pop('instance', None)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['supplies'] = OfficeSupply.objects.all().select_related('unit')
        return context

    def form_valid(self, form):
        items = form.cleaned_data.get('items', [])
        if not items:
            messages.error(self.request, 'Must select at least one item')
            return self.form_invalid(form)
        
        # Calculate total quantity for main request
        total_quantity = sum(item['quantity'] for item in items)
        
        # Create main request with total quantity
        request = OfficeSupplyRequest.objects.create(
            requester=self.request.user,
            purpose=form.cleaned_data['purpose'],
            is_bulk=True,
            quantity=total_quantity,  # Add this line
            supply=OfficeSupply.objects.get(id=items[0]['id'])  # Use first item as main supply
        )
        
        # Create request items
        for item in items:
            try:
                supply = OfficeSupply.objects.get(id=item['id'])
                RequestItem.objects.create(
                    request=request,
                    supply=supply,
                    quantity=item['quantity']
                )
            except OfficeSupply.DoesNotExist:
                continue
        
        messages.success(self.request, 'Request submitted successfully.')
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

class RequestApproveView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = OfficeSupplyRequest
    fields = ['status', 'approved_by']  # Removed total_cost and invoice_number
    template_name = 'office_supplies/approve_form.html'
    success_url = reverse_lazy('office-request-list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def form_valid(self, form):
        old_status = self.get_object().status
        new_status = form.cleaned_data['status']
        supply = form.instance.supply
        ordered_qty = form.instance.quantity
        
        # Create movement record for status change
        if (old_status != new_status):
            action = 'request_approved' if new_status == 'approved' else 'request_rejected'
            InventoryMovement.objects.create(
                content_type=ContentType.objects.get_for_model(supply),
                object_id=supply.id,
                action=action,
                quantity=ordered_qty,
                previous_quantity=supply.quantity,
                item_type='office',
                item_name=supply.name,
                category=supply.category.name,
                unit=supply.unit
            )

            if (new_status == 'approved'):
                if (supply.quantity < ordered_qty):
                    messages.error(self.request, f'Insufficient stock. Only {supply.quantity} {supply.unit} available.')
                    return self.form_invalid(form)

                supply.quantity -= ordered_qty
                supply.save()
                form.instance.approved_by = self.request.user
                messages.success(self.request, f'Request approved and {ordered_qty} {supply.unit} deducted from inventory.')

        return super().form_valid(form)

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have permission to approve requests.')
        return redirect('office-requests')

    def get_queryset(self):
        return super().get_queryset().select_related(
            'supply', 'requester'
        ).prefetch_related(
            'items__supply__category',
            'items__supply__unit'
        )

class RequestListView(LoginRequiredMixin, ListView):
    model = OfficeSupplyRequest
    template_name = 'office_supplies/request_list.html'
    context_object_name = 'requests'
    paginate_by = 20

    def get_queryset(self):
        return OfficeSupplyRequest.objects.select_related(
            'supply', 'requester', 'approved_by'
        ).order_by('-request_date')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_count'] = self.get_queryset().filter(status='pending').count()
        return context

class RequestDetailView(LoginRequiredMixin, DetailView):
    model = OfficeSupplyRequest
    template_name = 'office_supplies/request_detail.html'
    context_object_name = 'request'

    def get_queryset(self):
        return super().get_queryset().select_related(
            'supply', 'requester', 'approved_by'
        ).prefetch_related('items__supply__category', 'items__supply__unit')

class SupplyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = OfficeSupply
    form_class = OfficeSupplyForm
    template_name = 'office_supplies/form.html'
    success_url = reverse_lazy('office-supply-list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        # Store current values before save
        self.object = form.instance
        old_instance = OfficeSupply.objects.get(pk=self.object.pk)  # Fixed syntax here
        
        # Save new values
        response = super().form_valid(form)
        
        # Create movement record if non-quantity fields changed
        if any(getattr(self.object, field) != getattr(old_instance, field) 
               for field in ['name', 'category', 'unit', 'notes', 'expiration_date']):
            InventoryMovement.objects.create(
                content_type=ContentType.objects.get_for_model(self.object),
                object_id=self.object.id,
                action='updated',
                quantity=self.object.quantity,
                previous_quantity=old_instance.quantity,
                item_type='office',
                item_name=self.object.name,
                category=self.object.category.name,
                unit=self.object.unit
            )
        
        messages.success(self.request, f'Supply "{form.instance.name}" has been updated.')
        return response

class CategoryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = OfficeSupplyCategory
    fields = ['name', 'description']
    template_name = 'office_supplies/category_form.html'
    success_url = '/office-supplies/'

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" has been created.')
        return super().form_valid(form)

class BulkSupplyUploadView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'office_supplies/bulk_upload.html'
    form_class = BulkSupplyUploadForm
    success_url = reverse_lazy('office-supply-list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        csv_file = form.cleaned_data['file']
        decoded_file = csv_file.read().decode('utf-8')
        csv_data = csv.DictReader(io.StringIO(decoded_file))
        
        success_count = 0
        error_count = 0
        errors = []
        
        required_fields = ['name', 'category', 'quantity', 'unit']
        
        # Validate header
        headers = csv_data.fieldnames
        if not headers or not all(field in headers for field in required_fields):
            messages.error(self.request, 'Invalid CSV format. Required columns: name, category, quantity, unit')
            return super().form_invalid(form)

        # Add unit name mapping
        UNIT_MAPPING = {
            'piece': 'pcs',
            'pieces': 'pcs',
            'pc': 'pcs',
            'pcs': 'pcs',
            'box': 'boxes',
            'ream': 'reams',
            'pack': 'packs',
            'roll': 'rolls',
            'bottle': 'bottles',
            'cartridge': 'cartridges',
            'set': 'sets'
        }

        for row_num, row in enumerate(csv_data, start=2):  # Start from 2 for excel row numbers
            try:
                # Validate required fields
                if not all(row.get(field) for field in required_fields):
                    errors.append(f'Row {row_num}: Missing required fields')
                    error_count += 1
                    continue

                # Improved unit validation with mapping
                unit_name = row['unit'].lower().strip()
                unit_name = UNIT_MAPPING.get(unit_name, unit_name)  # Get mapped name or keep original
                
                unit = UnitMeasure.objects.filter(name=unit_name).first()
                if not unit:
                    errors.append(f'Row {row_num}: Invalid unit "{row["unit"]}". Valid units: {", ".join(UnitMeasure.objects.values_list("display_name", flat=True))}')
                    error_count += 1
                    continue

                # Validate quantity
                try:
                    quantity = int(row['quantity'])
                    if quantity < 0:
                        raise ValueError
                except ValueError:
                    errors.append(f'Row {row_num}: Invalid quantity')
                    error_count += 1
                    continue

                # Validate reorder level
                reorder_level = 10
                if row.get('reorder_level'):
                    try:
                        reorder_level = int(row['reorder_level'])
                        if reorder_level < 0:
                            raise ValueError
                    except ValueError:
                        errors.append(f'Row {row_num}: Invalid reorder level')
                        error_count += 1
                        continue

                # Create category if needed
                category, _ = OfficeSupplyCategory.objects.get_or_create(
                    name=row['category']
                )
                
                # Create supply
                OfficeSupply.objects.create(
                    name=row['name'].strip(),
                    category=category,
                    quantity=quantity,
                    unit=unit,
                    reorder_level=reorder_level,
                    notes=row.get('notes', '').strip()
                )
                success_count += 1
                
            except Exception as e:
                errors.append(f'Row {row_num}: {str(e)}')
                error_count += 1

        # Show detailed error messages
        if errors:
            messages.warning(self.request, 'Import completed with errors:')
            for error in errors[:5]:  # Show first 5 errors
                messages.error(self.request, error)
            if len(errors) > 5:
                messages.error(self.request, f'...and {len(errors) - 5} more errors')

        messages.success(self.request, 
            f'Successfully added {success_count} items. Failed: {error_count}')
        return super().form_valid(form)

class LowStockListView(LoginRequiredMixin, ListView):
    model = OfficeSupply
    template_name = 'office_supplies/list.html'
    context_object_name = 'supplies'

    def get_queryset(self):
        return OfficeSupply.objects.filter(quantity__lte=F('reorder_level'))

class ExpiringListView(LoginRequiredMixin, ListView):
    model = OfficeSupply
    template_name = 'office_supplies/list.html'
    context_object_name = 'supplies'

    def get_queryset(self):
        today = timezone.now().date()
        thirty_days = today + timezone.timedelta(days=30)
        return OfficeSupply.objects.filter(
            expiration_date__gt=today,
            expiration_date__lte=thirty_days
        )

class SupplyDetailView(LoginRequiredMixin, DetailView):
    model = OfficeSupply
    template_name = 'office_supplies/detail.html'
    context_object_name = 'supply'

    def get_queryset(self):
        return super().get_queryset().select_related('category', 'unit')