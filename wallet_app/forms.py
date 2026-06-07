from django import forms
from .models import Deposit, Product


class DepositForm(forms.ModelForm):
    class Meta:
        model = Deposit
        fields = ['amount', 'upi_id', 'account_name']
        widgets = {
            'upi_id': forms.TextInput(attrs={'placeholder': 'name@upi'}),
            'account_name': forms.TextInput(attrs={'placeholder': 'Account holder name'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-milky-500 focus:border-transparent',
            })


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'investment_amount', 'daily_return', 'duration_days', 'total_income', 'image', 'active']
        widgets = {
            'active': forms.CheckboxInput(),
        }
        labels = {
            'name': 'Product Name',
            'investment_amount': 'Price (INR)',
            'daily_return': 'Daily Income (INR)',
            'duration_days': 'Duration (Days)',
            'total_income': 'Total Income (INR)',
            'image': 'Product Image',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'active':
                field.widget.attrs.update({
                    'class': 'w-full rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-milky-500 focus:border-transparent',
                })
            field.widget.attrs.setdefault('placeholder', field.label)
