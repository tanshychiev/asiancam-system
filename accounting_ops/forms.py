from django import forms

from accounting.models import ChartOfAccount
from .models import (
    BankAccount,
    BankDeposit,
    BankReconcile,
    BankRule,
    LandedCostAllocation,
)


class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = [
            "name",
            "bank_name",
            "account_number",
            "currency",
            "chart_account",
            "opening_balance",
            "memo",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields["chart_account"].queryset = ChartOfAccount.objects.filter(
                company=company,
                is_active=True,
                is_group=False,
            ).order_by("code")
        else:
            self.fields["chart_account"].queryset = ChartOfAccount.objects.none()


class BankDepositForm(forms.ModelForm):
    class Meta:
        model = BankDeposit
        fields = [
            "deposit_date",
            "number",
            "deposit_to",
            "source_account",
            "amount",
            "memo",
            "status",
        ]
        widgets = {
            "deposit_date": forms.DateInput(attrs={"type": "date"}),
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields["deposit_to"].queryset = BankAccount.objects.filter(
                company=company,
                is_active=True,
            ).order_by("name")

            self.fields["source_account"].queryset = ChartOfAccount.objects.filter(
                company=company,
                is_active=True,
                is_group=False,
            ).order_by("code")
        else:
            self.fields["deposit_to"].queryset = BankAccount.objects.none()
            self.fields["source_account"].queryset = ChartOfAccount.objects.none()


class BankRuleForm(forms.ModelForm):
    class Meta:
        model = BankRule
        fields = [
            "name",
            "priority_order",
            "money_direction",
            "keyword",
            "target_account",
            "memo",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields["target_account"].queryset = ChartOfAccount.objects.filter(
                company=company,
                is_active=True,
                is_group=False,
            ).order_by("code")
        else:
            self.fields["target_account"].queryset = ChartOfAccount.objects.none()


class BankReconcileForm(forms.ModelForm):
    class Meta:
        model = BankReconcile
        fields = [
            "bank_account",
            "reconcile_date",
            "tran_date",
            "bank_balance",
            "book_balance",
            "memo",
        ]
        widgets = {
            "reconcile_date": forms.DateInput(attrs={"type": "date"}),
            "tran_date": forms.DateInput(attrs={"type": "date"}),
            "bank_balance": forms.NumberInput(attrs={"step": "0.01"}),
            "book_balance": forms.NumberInput(attrs={"step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields["bank_account"].queryset = BankAccount.objects.filter(
                company=company,
                is_active=True,
            ).order_by("name")
        else:
            self.fields["bank_account"].queryset = BankAccount.objects.none()


class LandedCostAllocationForm(forms.ModelForm):
    class Meta:
        model = LandedCostAllocation
        fields = [
            "allocation_date",
            "number",
            "purchase_date",
            "bill_no",
            "vendor_name",
            "po_number",
            "allocation_method",
            "landed_cost_account",
            "clearing_account",
            "amount",
            "memo",
            "status",
        ]
        widgets = {
            "allocation_date": forms.DateInput(attrs={"type": "date"}),
            "purchase_date": forms.DateInput(attrs={"type": "date"}),
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

        if company:
            accounts = ChartOfAccount.objects.filter(
                company=company,
                is_active=True,
                is_group=False,
            ).order_by("code")

            self.fields["landed_cost_account"].queryset = accounts
            self.fields["clearing_account"].queryset = accounts
        else:
            self.fields["landed_cost_account"].queryset = ChartOfAccount.objects.none()
            self.fields["clearing_account"].queryset = ChartOfAccount.objects.none()


class ImportUploadForm(forms.Form):
    file = forms.FileField(required=True)