
from django import forms
from .models import Deposit


UPI_METHOD_CHOICES = [
    ('Google Pay', 'Google Pay'),
    ('PhonePe', 'PhonePe'),
    ('Paytm UPI', 'Paytm UPI'),
    ('BHIM', 'BHIM'),
]


class DepositForm(forms.ModelForm):
    PRESET_AMOUNTS = [100, 500, 1000, 5000, 10000]

    amount = forms.DecimalField(
        min_value=1,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'placeholder': 'Enter amount'})
    )
    upi_id = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'name@upi'})
    )
    upi_method = forms.ChoiceField(
        choices=UPI_METHOD_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-milky-500 focus:border-transparent'})
    )

    class Meta:
        model = Deposit
        fields = ['amount', 'upi_id']
