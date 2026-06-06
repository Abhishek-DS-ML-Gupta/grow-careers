from django import forms
from .models import Deposit


class DepositForm(forms.ModelForm):
    class Meta:
        model = Deposit
        fields = ['amount', 'upi_id']
        widgets = {
            'upi_id': forms.TextInput(attrs={'placeholder': 'name@upi'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-milky-500 focus:border-transparent',
            })
