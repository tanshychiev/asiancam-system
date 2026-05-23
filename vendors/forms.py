from django import forms

from accounting.models import ChartOfAccount
from .models import Vendor, VendorTransaction


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = [
            "name",
            "phone",
            "email",
            "contact_person",
            "address",
            "opening_balance",
            "memo",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Vendor name",
            }),
            "phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Phone number",
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Email",
            }),
            "contact_person": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Contact person",
            }),
            "address": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Vendor address",
            }),
            "opening_balance": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
            }),
            "memo": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Memo / note",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }


class VendorTransactionForm(forms.ModelForm):
    class Meta:
        model = VendorTransaction
        fields = [
            "vendor",
            "transaction_type",
            "transaction_date",
            "number",
            "po_number",
            "debit_account",
            "credit_account",
            "amount",
            "memo",
            "status",
        ]

        widgets = {
            "vendor": forms.Select(attrs={
                "class": "form-control",
            }),
            "transaction_type": forms.Select(attrs={
                "class": "form-control",
            }),
            "transaction_date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control",
            }),
            "number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Number / bill no",
            }),
            "po_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "PO number",
            }),
            "debit_account": forms.Select(attrs={
                "class": "form-control",
            }),
            "credit_account": forms.Select(attrs={
                "class": "form-control",
            }),
            "amount": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
                "placeholder": "0.00",
            }),
            "memo": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Memo / description",
            }),
            "status": forms.Select(attrs={
                "class": "form-control",
            }),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)
        transaction_type = kwargs.pop("transaction_type", None)

        super().__init__(*args, **kwargs)

        if company:
            self.fields["vendor"].queryset = Vendor.objects.filter(
                company=company,
                is_active=True,
            ).order_by("name")

            self.fields["debit_account"].queryset = ChartOfAccount.objects.filter(
                company=company,
                is_active=True,
                is_group=False,
            ).order_by("code")

            self.fields["credit_account"].queryset = ChartOfAccount.objects.filter(
                company=company,
                is_active=True,
                is_group=False,
            ).order_by("code")
        else:
            self.fields["vendor"].queryset = Vendor.objects.none()
            self.fields["debit_account"].queryset = ChartOfAccount.objects.none()
            self.fields["credit_account"].queryset = ChartOfAccount.objects.none()

        if transaction_type:
            self.fields["transaction_type"].initial = transaction_type

        self.fields["vendor"].required = False

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")

        if amount is None or amount <= 0:
            raise forms.ValidationError("Amount must be more than zero.")

        return amount

    def clean(self):
        cleaned_data = super().clean()

        debit_account = cleaned_data.get("debit_account")
        credit_account = cleaned_data.get("credit_account")

        if debit_account and credit_account and debit_account == credit_account:
            raise forms.ValidationError("Debit account and credit account cannot be the same.")

        return cleaned_data