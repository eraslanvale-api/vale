import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from accounts.utils import send_verification_email

print("Testing send_verification_email...")
try:
    # Use the same email as the successful shell test
    result = send_verification_email('teknoktay@gmail.com', '1234')
    print(f"Result: {result}")
except Exception as e:
    print(f"Exception caught in reproduction script: {e}")
