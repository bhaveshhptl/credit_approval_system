from decimal import Decimal
from datetime import datetime, date
from django.utils import timezone
from .models import Customer, Loan

class CreditScoreCalculator:
    @staticmethod
    def calculate_credit_score(customer_id):
        try:
            customer = Customer.objects.get(customer_id=customer_id)
            loans = Loan.objects.filter(customer=customer)
            
            if not loans.exists():
                return 50  
            
            # Component 1: Past Loans paid on time (40% weight)
            on_time_score = CreditScoreCalculator._calculate_on_time_score(loans)
            
            # Component 2: Number of loans taken (20% weight)
            loan_count_score = CreditScoreCalculator._calculate_loan_count_score(loans)
            
            # Component 3: Loan activity in current year (20% weight)
            current_year_score = CreditScoreCalculator._calculate_current_year_score(loans)
            
            # Loan approved volume (20% weight)
            volume_score = CreditScoreCalculator._calculate_volume_score(loans, customer)
            
            # Calculate weighted score
            credit_score = (
                on_time_score * 0.4 +
                loan_count_score * 0.2 +
                current_year_score * 0.2 +
                volume_score * 0.2
            )
            
            # Check if current loans > approved limit
            current_debt = sum(loan.monthly_repayment for loan in loans if loan.is_active)
            if current_debt > customer.approved_limit:
                return 0
            
            return min(100, max(0, int(credit_score)))
            
        except Customer.DoesNotExist:
            return 0
    
    @staticmethod
    def _calculate_on_time_score(loans):
        total_emis = sum(loan.emis_paid_on_time + (loan.tenure - loan.emis_paid_on_time) for loan in loans)
        on_time_emis = sum(loan.emis_paid_on_time for loan in loans)
        
        if total_emis == 0:
            return 50
        
        return (on_time_emis / total_emis) * 100
    
    @staticmethod
    def _calculate_loan_count_score(loans):
        loan_count = loans.count()
        if loan_count <= 2:
            return 100
        elif loan_count <= 5:
            return 75
        elif loan_count <= 10:
            return 50
        else:
            return 25
    
    @staticmethod
    def _calculate_current_year_score(loans):
        current_year = timezone.now().year
        current_year_loans = loans.filter(start_date__year=current_year)
        
        if current_year_loans.count() == 0:
            return 100
        elif current_year_loans.count() <= 2:
            return 75
        elif current_year_loans.count() <= 4:
            return 50
        else:
            return 25
    
    @staticmethod
    def _calculate_volume_score(loans, customer):
        total_loan_amount = sum(loan.loan_amount for loan in loans)
        if total_loan_amount <= customer.approved_limit * Decimal('0.5'):
            return 100
        elif total_loan_amount <= customer.approved_limit:
            return 75
        elif total_loan_amount <= customer.approved_limit * Decimal('1.5'):
            return 50
        else:
            return 25

class LoanCalculator:
    @staticmethod
    def calculate_monthly_installment(principal: Decimal, annual_rate: Decimal, tenure_months: int) -> Decimal:
        """Calculate EMI using compound interest formula."""
        monthly_rate = annual_rate / (Decimal('12') * Decimal('100'))
        if monthly_rate == 0:
            return principal / tenure_months
        
        factor = (Decimal('1') + monthly_rate) ** tenure_months
        emi = principal * monthly_rate * factor / (factor - Decimal('1'))
        return emi.quantize(Decimal('0.00')) 
    
    @staticmethod
    def get_corrected_interest_rate(credit_score):
        """Get minimum interest rate based on credit score"""
        if credit_score > 50:
            return None  
        elif 30 < credit_score <= 50:
            return 12.0
        elif 10 < credit_score <= 30:
            return 16.0
        else:
            return None  
