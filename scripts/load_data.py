import os
import sys
import django
from api.models import Customer, Loan
from api.tasks import load_customer_data, load_loan_data

sys.path.append('/app')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'credit_system.settings')
django.setup()


if __name__ == '__main__':
    if Customer.objects.exists() and Loan.objects.exists():
        print("Customers already loaded, skipping ingestion.")
    else:
        print("Loading customer data...")
        result1 = load_customer_data()
        print(result1)
        print("Loading loan data...")
        result2 = load_loan_data()
        print(result2)
        print("Data loading completed!")
