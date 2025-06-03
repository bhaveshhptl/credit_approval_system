from celery import shared_task
import pandas as pd
from django.conf import settings
from .models import Customer, Loan
import os

@shared_task
def load_customer_data():
    """Load customer data from Excel file"""
    try:
        file_path = os.path.join(settings.BASE_DIR, 'data', 'customer_data.xlsx')
        df = pd.read_excel(file_path)
        
        customers_created = 0
        for _, row in df.iterrows():
            customer, created = Customer.objects.update_or_create(
                customer_id=row['Customer ID'],
                defaults={
                    'first_name': row['First Name'],
                    'last_name': row['Last Name'],
                    'age': row['Age'],
                    'phone_number': row['Phone Number'],
                    'monthly_salary': row['Monthly Salary'],
                    'approved_limit': row['Approved Limit'],
                }
            )
            
            if created:
                customers_created += 1
        
        return f"Successfully loaded {customers_created} customers"
    
    except Exception as e:
        return f"Error loading customer data: {str(e)}"

@shared_task
def load_loan_data():
    """Load loan data from Excel file"""
    try:
        file_path = os.path.join(settings.BASE_DIR, 'data', 'loan_data.xlsx')
        df = pd.read_excel(file_path)
        
        loans_created = 0
        for _, row in df.iterrows():
            try:
                customer = Customer.objects.get(customer_id = row['Customer ID'])
                
                start_date = pd.to_datetime(row['Date of Approval']).date()
                end_date = pd.to_datetime(row['End Date']).date()
                
                loan, created = Loan.objects.get_or_create(
                    loan_id=row['Loan ID'],
                    defaults={
                        'customer': customer,
                        'loan_amount': row['Loan Amount'],
                        'tenure': row['Tenure'],
                        'interest_rate': row['Interest Rate'],
                        'monthly_repayment': row['Monthly payment'],
                        'emis_paid_on_time': row['EMIs paid on Time'],
                        'start_date': start_date,
                        'end_date': end_date,
                    }
                )
                if created:
                    loans_created += 1
                    
            except Customer.DoesNotExist:
                continue  
        
        return f"Successfully loaded {loans_created} loans"
    
    except Exception as e:
        return f"Error loading loan data: {str(e)}"
