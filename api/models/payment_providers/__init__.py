from .paystack import PaystackProvider

PROVIDER_MAPPING = {
    'paystack': PaystackProvider,
    # Add more providers as they are implemented
    # 'moniepoint': MoniepointProvider,
    # 'flutterwave': FlutterwaveProvider,
} 