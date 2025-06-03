from rest_framework import serializers
from .models import Customer, Loan

class CustomerRegistrationSerializer(serializers.ModelSerializer):
    age = serializers.IntegerField(min_value=18, max_value=100)
    monthly_income = serializers.DecimalField(max_digits=10, decimal_places=2, source='monthly_salary')
    
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'age', 'monthly_income', 'phone_number']
    
    def create(self, validated_data):
        
        # approved limit: 36 * monthly_salary rounded to nearest lakh
        monthly_salary = validated_data['monthly_salary']
        approved_limit = round((36 * monthly_salary) / 100000) * 100000
        validated_data['approved_limit'] = approved_limit
        return super().create(validated_data)

class CustomerResponseSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    monthly_income = serializers.DecimalField(max_digits=10, decimal_places=2, source='monthly_salary', read_only=True)
    
    class Meta:
        model = Customer
        fields = ['customer_id', 'name', 'age', 'monthly_income', 'approved_limit', 'phone_number']

class LoanEligibilityRequestSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    tenure = serializers.IntegerField(min_value=1, max_value=360)  # 1 to 30 years

class LoanEligibilityResponseSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    approval = serializers.BooleanField()
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    corrected_interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    tenure = serializers.IntegerField()
    monthly_installment = serializers.DecimalField(max_digits=10, decimal_places=2)

class CreateLoanRequestSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    tenure = serializers.IntegerField()

class CreateLoanResponseSerializer(serializers.Serializer):
    loan_id = serializers.IntegerField(allow_null=True)
    customer_id = serializers.IntegerField()
    loan_approved = serializers.BooleanField()
    message = serializers.CharField()
    monthly_installment = serializers.DecimalField(max_digits=10, decimal_places=2)