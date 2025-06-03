from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Max
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from .models import Customer, Loan
from .serializers import (
    CustomerRegistrationSerializer, 
    CustomerResponseSerializer,
    LoanEligibilityRequestSerializer,
    LoanEligibilityResponseSerializer,
    CreateLoanRequestSerializer, 
    CreateLoanResponseSerializer
)
from .utils import CreditScoreCalculator, LoanCalculator

@api_view(['POST'])
def register_customer(request):
    """Register a new customer"""
    serializer = CustomerRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        customer = serializer.save()
        response_serializer = CustomerResponseSerializer(customer)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def check_eligibility(request):
    """Check loan eligibility for a customer"""
    serializer = LoanEligibilityRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    customer_id = data['customer_id']
    loan_amount = data['loan_amount']
    interest_rate = data['interest_rate']
    tenure = data['tenure']
    
    try:
        customer = Customer.objects.get(customer_id=customer_id)
    except Customer.DoesNotExist:
        return Response(
            {'error': 'Customer not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # credit score
    credit_score = CreditScoreCalculator.calculate_credit_score(customer_id)
    
    # current EMI burden
    active_loans = Loan.objects.filter(customer=customer, end_date__gte=timezone.now().date())
    current_emi_sum = sum(loan.monthly_repayment for loan in active_loans)
    
    # if current EMIs > 50% of monthly salary
    if current_emi_sum > customer.monthly_salary * Decimal('0.5'):
        return Response({
            'customer_id': customer_id,
            'approval': False,
            'interest_rate': interest_rate,
            'corrected_interest_rate': interest_rate,
            'tenure': tenure,
            'monthly_installment': 0,
            'message': 'Current EMI burden exceeds 50% of monthly salary'
        })
    
    approval = False
    corrected_interest_rate = interest_rate
    
    if credit_score > 50:
        approval = True
    elif 30 < credit_score <= 50:
        approval = True
        corrected_interest_rate = max(interest_rate, Decimal('12.0'))
    elif 10 < credit_score <= 30:
        approval = True
        corrected_interest_rate = max(interest_rate, Decimal('16.0'))
    else:
        approval = False
    
    monthly_installment = 0
    if approval:
        monthly_installment = LoanCalculator.calculate_monthly_installment(
            loan_amount,
            corrected_interest_rate, 
            tenure
        )
    
    response_data = {
        'customer_id': customer_id,
        'approval': approval,
        'interest_rate': interest_rate,
        'corrected_interest_rate': corrected_interest_rate,
        'tenure': tenure,
        'monthly_installment': monthly_installment
    }

    serializer = LoanEligibilityResponseSerializer(response_data)
    return Response(serializer.data)



@api_view(['POST'])
def create_loan(request):
    serializer = CreateLoanRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    data = serializer.validated_data
    customer_id = data['customer_id']
    loan_amount = data['loan_amount']
    interest_rate = data['interest_rate']
    tenure = data['tenure']
    try:
        customer = Customer.objects.get(customer_id=customer_id)
    except Customer.DoesNotExist:
        return Response({
            "loan_id": None,
            "customer_id": customer_id,
            "loan_approved": False,
            "message": "Customer not found",
            "monthly_installment": 0
        }, status=status.HTTP_404_NOT_FOUND)
    
    credit_score = CreditScoreCalculator.calculate_credit_score(customer_id)
    active_loans = Loan.objects.filter(customer=customer, end_date__gte=timezone.now().date())
    current_emi_sum = sum(loan.monthly_repayment for loan in active_loans)
    max_emi = customer.monthly_salary * Decimal('0.5')
    monthly_installment = LoanCalculator.calculate_monthly_installment(loan_amount, interest_rate, tenure)

    loan_approved = False
    message = ""
    max_id = Loan.objects.aggregate(max_id=Max('loan_id'))['max_id'] or 0
    new_loan_id = max_id + 1

    if current_emi_sum + monthly_installment > max_emi:
        message = "Loan denied: EMI burden exceeds 50% of monthly salary."
    elif credit_score <= 10:
        message = "Loan denied: Credit score too low."
    else:
        loan_approved = True
        message = "Loan approved."
        # Create Loan
        today = timezone.now().date()
        end_date = today + relativedelta(months=tenure)
        loan = Loan.objects.create(
            customer=customer,
            loan_amount=loan_amount,
            tenure=tenure,
            interest_rate=interest_rate,
            monthly_repayment=monthly_installment,
            emis_paid_on_time=0,
            start_date=today,
            end_date=end_date
        )
        loan_id = new_loan_id
        customer.current_debt += loan_amount
        customer.save()

    response_data = {
            'loan_id': loan_id,
            'customer_id': customer_id,
            'loan_approved': loan_approved,
            'message': message,
            'monthly_installment': monthly_installment if loan_approved else 0
    }
    serializer = CreateLoanResponseSerializer(response_data)
    return Response(serializer.data)


@api_view(['GET'])
def view_loan(request, loan_id):
    try:
        loan = Loan.objects.get(loan_id=loan_id)
        customer = loan.customer
        data = {
            "loan_id": loan.loan_id,
            "customer": {
                "id": customer.customer_id,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "phone_number": customer.phone_number,
                "age": customer.age,
            },
            "loan_amount": loan.loan_amount,
            "interest_rate": loan.interest_rate,
            "monthly_installment": loan.monthly_repayment,
            "tenure": loan.tenure,
        }
        return Response(data)
    except Loan.DoesNotExist:
        return Response({"error": "Loan not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def view_loans_by_customer(request, customer_id):
    try:
        customer = Customer.objects.get(customer_id=customer_id)
        loans = Loan.objects.filter(customer=customer)
        today = timezone.now().date()
        result = []
        for loan in loans:
            months_passed = (today.year - loan.start_date.year) * 12 + (today.month - loan.start_date.month)
            repayments_left = max(loan.tenure - months_passed, 0)
            result.append({
                "loan_id": loan.loan_id,
                "loan_amount": loan.loan_amount,
                "interest_rate": loan.interest_rate,
                "monthly_installment": loan.monthly_repayment,
                "repayments_left": repayments_left
            })
        return Response(result)
    except Customer.DoesNotExist:
        return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
