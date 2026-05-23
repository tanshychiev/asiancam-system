from django import forms

from accounting.models import ChartOfAccount
from .models import (
    Customer,
    CustomerTransaction,
    CustomerType,
    PriceLevel,
    Region,
    SalesDocument,
    Salesperson,
)


class CustomerTypeForm(forms.ModelForm):
    class Meta:
        model = CustomerType
        fields = ["name", "credit_limit", "credit_term", "memo", "is_active"]


class SalespersonForm(forms.ModelForm):
    class Meta:
        model = Salesperson
        fields = ["name", "code", "local_name", "phone", "email", "memo", "is_active"]


class PriceLevelForm(forms.ModelForm):
    class Meta:
        model = PriceLevel
        fields = [
            "name",
            "mode",
            "value",
            "round_type",
            "discount_method",
            "price_level_type",
            "memo",
            "is_active",
        ]


class RegionForm(forms.ModelForm):
    class Meta:
        model = Region
        fields = ["name", "code", "local_name", "memo", "is_active"]


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            "name",
            "code",
            "local_name",
            "phone",
            "email",
            "telegram",
            "address",
            "customer_type",
            "salesperson",
            "price_level",
            "region",
            "opening_balance",
            "memo",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields["customer_type"].queryset = CustomerType.objects.filter(company=company, is_active=True)
            self.fields["salesperson"].queryset = Salesperson.objects.filter(company=company, is_active=True)
            self.fields["price_level"].queryset = PriceLevel.objects.filter(company=company, is_active=True)
            self.fields["region"].queryset = Region.objects.filter(company=company, is_active=True)
        else:
            self.fields["customer_type"].queryset = CustomerType.objects.none()
            self.fields["salesperson"].queryset = Salesperson.objects.none()
            self.fields["price_level"].queryset = PriceLevel.objects.none()
            self.fields["region"].queryset = Region.objects.none()


class CustomerTransactionForm(forms.ModelForm):
    class Meta:
        model = CustomerTransaction
        fields = [
            "customer",
            "transaction_type",
            "transaction_date",
            "number",
            "so_number",
            "currency",
            "exchange_rate",
            "debit_account",
            "credit_account",
            "amount",
            "memo",
            "status",
        ]

        widgets = {
            "transaction_date": forms.DateInput(attrs={"type": "date"}),
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "exchange_rate": forms.NumberInput(attrs={"step": "0.0001", "min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)
        transaction_type = kwargs.pop("transaction_type", None)

        super().__init__(*args, **kwargs)

        if company:
            self.fields["customer"].queryset = Customer.objects.filter(company=company, is_active=True).order_by("name")

            accounts = ChartOfAccount.objects.filter(
                company=company,
                is_active=True,
                is_group=False,
            ).order_by("code")

            self.fields["debit_account"].queryset = accounts
            self.fields["credit_account"].queryset = accounts
        else:
            self.fields["customer"].queryset = Customer.objects.none()
            self.fields["debit_account"].queryset = ChartOfAccount.objects.none()
            self.fields["credit_account"].queryset = ChartOfAccount.objects.none()

        if transaction_type:
            self.fields["transaction_type"].initial = transaction_type

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")

        if amount is None or amount <= 0:
            raise forms.ValidationError("Amount must be more than zero.")

        return amount


class SalesDocumentForm(forms.ModelForm):
    class Meta:
        model = SalesDocument
        fields = [
            "customer",
            "number",
            "document_date",
            "delivery_date",
            "salesperson",
            "customer_code",
            "address_name",
            "currency",
            "grand_total",
            "memo",
            "status",
        ]

        widgets = {
            "document_date": forms.DateInput(attrs={"type": "date"}),
            "delivery_date": forms.DateInput(attrs={"type": "date"}),
            "grand_total": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)

        super().__init__(*args, **kwargs)

        if company:
            self.fields["customer"].queryset = Customer.objects.filter(company=company, is_active=True).order_by("name")
            self.fields["salesperson"].queryset = Salesperson.objects.filter(company=company, is_active=True).order_by("name")
        else:
            self.fields["customer"].queryset = Customer.objects.none()
            self.fields["salesperson"].queryset = Salesperson.objects.none()