from django import forms
from .models import OfficeSupply, OfficeSupplyRequest, RequestItem
from inventory.models import UnitMeasure
from django.forms import inlineformset_factory

class OfficeSupplyForm(forms.ModelForm):
    expiration_date = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'type': 'date',
        'class': 'form-control'
    }))

    class Meta:
        model = OfficeSupply
        fields = [
            'name', 'category', 'quantity', 'unit',
            'expiration_date', 'reorder_level', 'notes'
        ]
        widgets = {
            'expiration_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required': False}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'unit': forms.Select(choices=[])  
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['unit'].queryset = UnitMeasure.objects.filter(is_active=True)

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
        model = OfficeSupplyRequest
        fields = ['supply', 'quantity', 'purpose', 'is_bulk']
        widgets = {
            'purpose': forms.Textarea(attrs={'rows': 3}),
            'is_bulk': forms.HiddenInput()
        }

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('is_bulk'):
            supply = cleaned_data.get('supply')
            quantity = cleaned_data.get('quantity')
            if supply and quantity and quantity > supply.quantity:
                raise forms.ValidationError(
                    f"Requested quantity ({quantity}) exceeds available stock ({supply.quantity})"
                )
        return cleaned_data

class BulkSupplyUploadForm(forms.Form):
    file = forms.FileField(
        label='CSV File',
        help_text='Upload CSV with columns: name,category,quantity,unit,reorder_level,notes'
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
                supply = OfficeSupply.objects.get(id=item['id'])
                if item['quantity'] > supply.quantity:
                    raise forms.ValidationError(
                        f"Insufficient stock for {supply.name}"
                    )
            except OfficeSupply.DoesNotExist:
                raise forms.ValidationError(f"Invalid supply selected")
        
        return items

RequestItemFormSet = inlineformset_factory(
    OfficeSupplyRequest,
    RequestItem,
    fields=('supply', 'quantity'),
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)
