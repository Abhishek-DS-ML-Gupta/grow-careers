from django.conf import settings


RAZORPAY_KEY_ID = getattr(settings, 'RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
RAZORPAY_WEBHOOK_SECRET = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')

UPI_METHODS = ['upi', 'googlepay', 'phonepe', 'paytm', 'bhim']
