from django import forms
from .models import VeterinarySupply, VeterinarySupplyRequest, RequestItem
from inventory.models import UnitMeasure

class VeterinarySupplyForm(forms.ModelForm):
    # Add optional expiration date field
    expiration_date = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'type': 'date',
        'class': 'form-control'
    }))
    
    class Meta:
        model = VeterinarySupply
        fields = [
            'name', 'category', 'quantity', 'unit',
            'expiration_date', 'reorder_level', 'notes'  # Changed from critical_stock
        ]
        labels = {
            'reorder_level': 'Low Stock Level',  # Updated label
        }
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'reorder_level': forms.NumberInput(attrs={'min': '0', 'class': 'form-control'}),
            'unit': forms.Select(choices=[])  # Will be populated dynamically
        }

class RequestForm(forms.ModelForm):
    status = forms.ChoiceField(
        choices=[
            ('pending', 'Pending Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = VeterinarySupplyRequest
        fields = ['status']

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('is_bulk'):
            supply = cleaned_data.get('supply')
            quantity = cleaned_data.get('quantity')
            if supply and quantity:
                if quantity > supply.quantity:
                    raise forms.ValidationError(
                        f"Requested quantity ({quantity}) exceeds available stock ({supply.quantity})"
                    )
        return cleaned_data

class BulkSupplyUploadForm(forms.Form):
    file = forms.FileField(
        label='CSV File',
        help_text='Upload CSV with columns: name,category,quantity,unit,expiration_date,notes'
    )

class BulkRequestForm(forms.Form):
    items = forms.JSONField(
        widget=forms.HiddenInput(),
        required=True,
        error_messages={'required': 'Must add at least one item'}
    )
    purpose = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3, 
            'class': 'form-control',
            'placeholder': 'Enter purpose for request'
        }),
        required=True
    )

    def clean_items(self):
        items = self.cleaned_data['items']
        if not items:
            raise forms.ValidationError("Must select at least one item")
        
        # Validate each item
        for item in items:
            if not all(k in item for k in ('id', 'quantity')):
                raise forms.ValidationError("Invalid item format")
            try:
                supply = VeterinarySupply.objects.get(id=item['id'])
                if item['quantity'] > supply.quantity:
                    raise forms.ValidationError(
                        f"Insufficient stock for {supply.name}"
                    )
            except VeterinarySupply.DoesNotExist:
                raise forms.ValidationError(f"Invalid supply selected")
        
        return items

from django.forms import inlineformset_factory

RequestItemFormSet = inlineformset_factory(
    VeterinarySupplyRequest,
    RequestItem,
    fields=('supply', 'quantity'),
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)
