from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages  
from django.contrib.contenttypes.models import ContentType
from django.db.models import F, Q  # Add this import
from django.urls import reverse_lazy
from django.utils import timezone
from .models import VeterinarySupply, VeterinarySupplyRequest, VeterinarySupplyCategory, RequestItem
from .forms import VeterinarySupplyForm, RequestForm, BulkSupplyUploadForm, RequestItemFormSet, BulkRequestForm  # Add this import
from reports.models import InventoryMovement
import csv
import io
from django.shortcuts import redirect
from django.core.exceptions import ValidationError
from inventory.models import UnitMeasure  # Add this import

class SupplyListView(LoginRequiredMixin, ListView):
    model = VeterinarySupply
    template_name = 'vet_supplies/list.html'
    context_object_name = 'supplies'
    paginate_by = 10  # Set pagination size

    def get_queryset(self):
        queryset = VeterinarySupply.objects.select_related('category').order_by('name')
        
        # Add search query
        search_query = self.request.GET.get('q')
        if (search_query):
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )
            
        # Stock status filter
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
        context['total_supplies'] = VeterinarySupply.objects.count()
        today = timezone.now().date()
        context['low_stock_count'] = VeterinarySupply.objects.filter(
            quantity__lte=F('reorder_level')  # Changed from critical_stock
        ).count()
        
        # Update expiring soon count to account for 2025 dates
        context['expiring_count'] = VeterinarySupply.objects.filter(
            expiration_date__gt=today,
            expiration_date__lte=today + timezone.timedelta(days=90)  # Extended window
        ).count()
        
        # Add out of stock count
        context['out_of_stock_count'] = VeterinarySupply.objects.filter(
            quantity=0
        ).count()
        
        # Add expired count
        context['expired_count'] = VeterinarySupply.objects.filter(
            expiration_date__lt=today
        ).count()
        
        context['is_staff'] = self.request.user.is_staff
        context['categories'] = VeterinarySupplyCategory.objects.all().order_by('name')
        return context

class SupplyCreateView(LoginRequiredMixin, CreateView):
    model = VeterinarySupply
    form_class = VeterinarySupplyForm
    template_name = 'vet_supplies/form.html'
    success_url = '/vet-supplies/'

    def form_valid(self, form):
        response = super().form_valid(form)
        # Log the initial creation with initial stock
        if form.cleaned_data['quantity'] > 0:
            InventoryMovement.objects.create(
                content_type=ContentType.objects.get_for_model(self.object),
                object_id=self.object.id,
                action='created',
                quantity=self.object.quantity,
                previous_quantity=0,
                item_type='vet',
                item_name=self.object.name,
                category=self.object.category.name,
                unit=self.object.unit
            )
        return response

class SupplyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = VeterinarySupply
    form_class = VeterinarySupplyForm
    template_name = 'vet_supplies/form.html'
    success_url = reverse_lazy('vet-supply-list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        # Store current values before save
        self.object = form.instance
        old_instance = VeterinarySupply.objects.get(pk=self.object.pk)
        
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
                item_type='vet',
                item_name=self.object.name,
                category=self.object.category.name,
                unit=self.object.unit
            )
        
        messages.success(self.request, f'Supply "{form.instance.name}" has been updated.')
        return response

class SupplyDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = VeterinarySupply
    template_name = 'vet_supplies/confirm_delete.html'
    success_url = reverse_lazy('supply-list')
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class SupplyDetailView(LoginRequiredMixin, DetailView):
    model = VeterinarySupply
    template_name = 'vet_supplies/detail.html'
    context_object_name = 'supply'

    def get_queryset(self):
        return super().get_queryset().select_related('category', 'unit')

class RequestCreateView(LoginRequiredMixin, CreateView):
    model = VeterinarySupplyRequest  
    template_name = 'vet_supplies/request_form.html'
    form_class = BulkRequestForm
    success_url = reverse_lazy('vet-request-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop('instance', None)  # Remove instance since BulkRequestForm is not a ModelForm
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['supplies'] = VeterinarySupply.objects.all().select_related('category', 'unit')
        return context

    def form_valid(self, form):
        items = form.cleaned_data.get('items', [])
        if not items:
            messages.error(self.request, 'Must select at least one item')
            return self.form_invalid(form)
        
        # Calculate total quantity for main request
        total_quantity = sum(item['quantity'] for item in items)
        
        # Create main request
        request = VeterinarySupplyRequest.objects.create(
            requester=self.request.user,
            purpose=form.cleaned_data['purpose'],
            is_bulk=True,
            quantity=total_quantity,  # Add total quantity
            supply=VeterinarySupply.objects.get(id=items[0]['id'])  # Use first item as main supply
        )
        
        # Create request items
        for item in items:
            try:
                supply = VeterinarySupply.objects.get(id=item['id'])
                RequestItem.objects.create(
                    request=request,
                    supply=supply,
                    quantity=item['quantity']
                )
            except VeterinarySupply.DoesNotExist:
                continue
        
        messages.success(self.request, 'Request submitted successfully.')
        return redirect(self.success_url)

class RequestDetailView(LoginRequiredMixin, DetailView):
    model = VeterinarySupplyRequest
    template_name = 'vet_supplies/request_detail.html'
    context_object_name = 'request'

class RequestListView(LoginRequiredMixin, ListView):
    model = VeterinarySupplyRequest
    template_name = 'vet_supplies/request_list.html'
    context_object_name = 'requests'
    paginate_by = 20

    def get_queryset(self):
        return VeterinarySupplyRequest.objects.select_related('supply', 'requester').order_by('-request_date')

class RequestUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = VeterinarySupplyRequest
    form_class = RequestForm
    template_name = 'vet_supplies/approve_form.html'
    success_url = reverse_lazy('vet-request-list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        old_status = self.get_object().status
        new_status = form.cleaned_data['status']
        request_obj = self.get_object()
        
        if old_status != new_status:
            if request_obj.is_bulk:
                # Handle bulk request items
                for item in request_obj.items.all():
                    if new_status == 'approved':
                        if item.quantity > item.supply.quantity:
                            messages.error(self.request, 
                                f'Insufficient stock for {item.supply.name}. Only {item.supply.quantity} {item.supply.unit} available.')
                            return self.form_invalid(form)
                        
                        # Create movement record and update stock
                        InventoryMovement.objects.create(
                            content_type=ContentType.objects.get_for_model(item.supply),
                            object_id=item.supply.id,
                            action='request_approved',
                            quantity=item.quantity,
                            previous_quantity=item.supply.quantity,
                            item_type='vet',
                            item_name=item.supply.name,
                            category=item.supply.category.name,
                            unit=item.supply.unit
                        )
                        
                        item.supply.quantity -= item.quantity
                        item.supply.save()
            else:
                # Handle single item request
                supply = request_obj.supply
                if new_status == 'approved':
                    if request_obj.quantity > supply.quantity:
                        messages.error(self.request, 
                            f'Insufficient stock. Only {supply.quantity} {supply.unit} available.')
                        return self.form_invalid(form)
                    
                    InventoryMovement.objects.create(
                        content_type=ContentType.objects.get_for_model(supply),
                        object_id=supply.id,
                        action='request_approved',
                        quantity=request_obj.quantity,
                        previous_quantity=supply.quantity,
                        item_type='vet',
                        item_name=supply.name,
                        category=supply.category.name,
                        unit=supply.unit
                    )
                    
                    supply.quantity -= request_obj.quantity
                    supply.save()

            # Update approval info
            form.instance.approval_date = timezone.now()
            form.instance.approved_by = self.request.user
            messages.success(self.request, f'Request {new_status} successfully.')

        return super().form_valid(form)

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have permission to approve requests.')
        return redirect('vet-request-list')

    def get_queryset(self):
        return super().get_queryset().select_related(
            'supply', 'requester'
        ).prefetch_related(
            'items__supply__category',
            'items__supply__unit'
        )

class CategoryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = VeterinarySupplyCategory
    fields = ['name', 'description']
    template_name = 'vet_supplies/category_form.html'
    success_url = '/vet-supplies/'

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" has been created.')
        return super().form_valid(form)

class BulkSupplyUploadView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'vet_supplies/bulk_upload.html'
    form_class = BulkSupplyUploadForm
    success_url = reverse_lazy('vet-supply-list')

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

        # Get valid units and mapping
        valid_units = set(UnitMeasure.objects.filter(is_active=True).values_list('name', flat=True))
        unit_mapping = {
            'vial': 'vials',
            'bottle': 'bottles',
            'box': 'boxes',
            'unit': 'units',
            'tablet': 'tablets',
            'tab': 'tablets',
            'tabs': 'tablets',
            'piece': 'pieces',
            'pc': 'pieces',
            'pcs': 'pieces',
            'ampule': 'ampoules',
            'amp': 'ampoules',
            'dose': 'doses',
            'sachet': 'sachets'
        }

        for row_num, row in enumerate(csv_data, start=2):
            try:
                # Validate required fields
                if not all(row.get(field) for field in required_fields):
                    errors.append(f'Row {row_num}: Missing required fields')
                    error_count += 1
                    continue

                # Clean and map unit name
                unit_name = row['unit'].lower().strip()
                unit_name = unit_mapping.get(unit_name, unit_name)
                
                # Get unit object
                unit = UnitMeasure.objects.filter(name=unit_name).first()
                if not unit:
                    errors.append(f'Row {row_num}: Invalid unit "{row["unit"]}". Valid units: {", ".join(sorted(valid_units))}')
                    error_count += 1
                    continue

                # Validate quantity
                try:
                    quantity = int(row['quantity'])
                    if quantity < 0:
                        raise ValueError
                except ValueError:
                    errors.append(f'Row {row_num}: Invalid quantity - must be a positive number')
                    error_count += 1
                    continue

                # Validate expiration date if provided
                expiration_date = None
                if row.get('expiration_date'):
                    try:
                        expiration_date = timezone.datetime.strptime(
                            row['expiration_date'].strip(), '%Y-%m-%d'
                        ).date()
                    except ValueError:
                        errors.append(f'Row {row_num}: Invalid date format - use YYYY-MM-DD')
                        error_count += 1
                        continue
                
                # Create category if needed
                category, _ = VeterinarySupplyCategory.objects.get_or_create(
                    name=row['category'].strip()
                )
                
                # Create supply with validated unit
                VeterinarySupply.objects.create(
                    name=row['name'].strip(),
                    category=category,
                    quantity=quantity,
                    unit=unit,  # Now unit is properly defined
                    expiration_date=expiration_date,
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
    model = VeterinarySupply
    template_name = 'vet_supplies/list.html'
    context_object_name = 'supplies'
    paginate_by = 10

    def get_queryset(self):
        return VeterinarySupply.objects.filter(
            quantity__lte=F('reorder_level')
        ).select_related('category').order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_supplies'] = VeterinarySupply.objects.count()
        today = timezone.now().date()
        context['low_stock_count'] = self.get_queryset().count()
        context['expiring_count'] = VeterinarySupply.objects.filter(
            expiration_date__gt=today,
            expiration_date__lte=today + timezone.timedelta(days=90)
        ).count()
        context['out_of_stock_count'] = VeterinarySupply.objects.filter(
            quantity=0
        ).count()
        context['expired_count'] = VeterinarySupply.objects.filter(
            expiration_date__lt=today
        ).count()
        context['categories'] = VeterinarySupplyCategory.objects.all().order_by('name')
        context['is_staff'] = self.request.user.is_staff
        return context

class ExpiringListView(LoginRequiredMixin, ListView):
    model = VeterinarySupply
    template_name = 'vet_supplies/list.html'
    context_object_name = 'supplies'

    def get_queryset(self):
        today = timezone.now().date()
        thirty_days = today + timezone.timedelta(days=30)
        return VeterinarySupply.objects.filter(
            expiration_date__gt=today,
            expiration_date__lte=thirty_days
        )