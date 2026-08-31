from django import forms
from django.forms import inlineformset_factory

from accounting.models import ChartOfAccount
from stock.models import Item
from .models import (
    PurchaseBill,
    PurchaseBillExpenseLine,
    PurchaseBillItemLine,
    Vendor,
    VendorTransaction,
)


def _company_accounts(company):
    if not company:
        return ChartOfAccount.objects.none()
    return ChartOfAccount.objects.filter(
        company=company,
        is_active=True,
        is_group=False,
    ).order_by("code", "name")


def find_default_ap_account(company):
    accounts = _company_accounts(company)
    return (
        accounts.filter(name__icontains="accounts payable").first()
        or accounts.filter(name__icontains="account payable").first()
        or accounts.filter(account_type=ChartOfAccount.ACCOUNT_TYPE_LIABILITY).first()
    )


def find_default_input_vat_account(company):
    accounts = _company_accounts(company)
    return (
        accounts.filter(name__icontains="input vat").first()
        or accounts.filter(name__icontains="vat input").first()
        or accounts.filter(name__icontains="input tax").first()
    )


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = [
            "code",
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
            "code": forms.TextInput(attrs={"class": "form-control", "placeholder": "Vendor ID / code"}),
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Vendor name"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone number"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"}),
            "contact_person": forms.TextInput(attrs={"class": "form-control", "placeholder": "Contact person"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Vendor address"}),
            "opening_balance": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "memo": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Memo / note"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip()
        if code and self.company:
            qs = Vendor.objects.filter(company=self.company, code__iexact=code)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("This vendor code already exists in this company.")
        return code


class VendorTransactionForm(forms.ModelForm):
    """Legacy transaction form retained for Cash Expense / Vendor Payment compatibility."""

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
            "vendor": forms.Select(attrs={"class": "form-control"}),
            "transaction_type": forms.Select(attrs={"class": "form-control"}),
            "transaction_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Number / bill no"}),
            "po_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "PO number"}),
            "debit_account": forms.Select(attrs={"class": "form-control"}),
            "credit_account": forms.Select(attrs={"class": "form-control"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0.01", "placeholder": "0.00"}),
            "memo": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Memo / description"}),
            "status": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)
        transaction_type = kwargs.pop("transaction_type", None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields["vendor"].queryset = Vendor.objects.filter(company=company, is_active=True).order_by("name")
            accounts = _company_accounts(company)
            self.fields["debit_account"].queryset = accounts
            self.fields["credit_account"].queryset = accounts
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


class PurchaseBillForm(forms.ModelForm):
    class Meta:
        model = PurchaseBill
        fields = [
            "vendor",
            "bill_date",
            "due_date",
            "number",
            "po_number",
            "accounts_payable_account",
            "input_vat_account",
            "memo",
        ]
        widgets = {
            "vendor": forms.Select(attrs={"class": "form-control", "id": "id_vendor"}),
            "bill_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "due_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Bill No."}),
            "po_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "PO Number"}),
            "accounts_payable_account": forms.Select(attrs={"class": "form-control"}),
            "input_vat_account": forms.Select(attrs={"class": "form-control"}),
            "memo": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Memo / note"}),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields["vendor"].queryset = Vendor.objects.filter(company=self.company, is_active=True).order_by("name")
            accounts = _company_accounts(self.company)
            self.fields["accounts_payable_account"].queryset = accounts
            self.fields["input_vat_account"].queryset = accounts

            if not self.is_bound and not self.instance.pk:
                ap = find_default_ap_account(self.company)
                vat = find_default_input_vat_account(self.company)
                if ap:
                    self.fields["accounts_payable_account"].initial = ap.pk
                if vat:
                    self.fields["input_vat_account"].initial = vat.pk
        else:
            self.fields["vendor"].queryset = Vendor.objects.none()
            self.fields["accounts_payable_account"].queryset = ChartOfAccount.objects.none()
            self.fields["input_vat_account"].queryset = ChartOfAccount.objects.none()

        self.fields["input_vat_account"].required = False

    def clean(self):
        data = super().clean()
        vendor = data.get("vendor")
        ap = data.get("accounts_payable_account")
        vat = data.get("input_vat_account")
        if self.company:
            if vendor and vendor.company_id != self.company.id:
                self.add_error("vendor", "Vendor must belong to the selected company.")
            if ap and ap.company_id != self.company.id:
                self.add_error("accounts_payable_account", "Account must belong to the selected company.")
            if vat and vat.company_id != self.company.id:
                self.add_error("input_vat_account", "Account must belong to the selected company.")
        return data


class PurchaseBillItemLineForm(forms.ModelForm):
    class Meta:
        model = PurchaseBillItemLine
        fields = ["item", "description", "qty", "unit_name", "unit_cost", "account", "vat_amount"]
        widgets = {
            "item": forms.Select(attrs={"class": "form-control item-select"}),
            "description": forms.TextInput(attrs={"class": "form-control", "placeholder": "Description"}),
            "qty": forms.NumberInput(attrs={"class": "form-control js-qty", "step": "0.01", "min": "0"}),
            "unit_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Unit"}),
            "unit_cost": forms.NumberInput(attrs={"class": "form-control js-unit-cost", "step": "0.01", "min": "0"}),
            "account": forms.Select(attrs={"class": "form-control"}),
            "vat_amount": forms.NumberInput(attrs={"class": "form-control js-vat", "step": "0.01", "min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields["item"].queryset = Item.objects.filter(company=company, is_active=True).select_related("unit_set", "inventory_account").order_by("code", "name")
            self.fields["account"].queryset = _company_accounts(company)
        else:
            self.fields["item"].queryset = Item.objects.none()
            self.fields["account"].queryset = ChartOfAccount.objects.none()
        self.fields["account"].required = False
        self.fields["description"].required = False
        self.fields["unit_name"].required = False


class PurchaseBillExpenseLineForm(forms.ModelForm):
    class Meta:
        model = PurchaseBillExpenseLine
        fields = ["description", "amount", "account", "vat_amount"]
        widgets = {
            "description": forms.TextInput(attrs={"class": "form-control", "placeholder": "Expense / service description"}),
            "amount": forms.NumberInput(attrs={"class": "form-control js-expense-amount", "step": "0.01", "min": "0"}),
            "account": forms.Select(attrs={"class": "form-control"}),
            "vat_amount": forms.NumberInput(attrs={"class": "form-control js-vat", "step": "0.01", "min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)
        self.fields["account"].queryset = _company_accounts(company) if company else ChartOfAccount.objects.none()


PurchaseBillItemLineFormSet = inlineformset_factory(
    PurchaseBill,
    PurchaseBillItemLine,
    form=PurchaseBillItemLineForm,
    extra=3,
    can_delete=True,
)

PurchaseBillExpenseLineFormSet = inlineformset_factory(
    PurchaseBill,
    PurchaseBillExpenseLine,
    form=PurchaseBillExpenseLineForm,
    extra=2,
    can_delete=True,
)

# =========================================================
# CUSTOMER REQUIREMENT PAYMENT FORM
# =========================================================
from .models import VendorPayment, VendorPaymentAllocation, VendorPaymentOtherCharge

class VendorPaymentForm(forms.ModelForm):
    class Meta:
        model=VendorPayment
        fields=["vendor","payment_date","number","payment_method","payment_account","accounts_payable_account","currency","memo"]
        widgets={
            "vendor":forms.Select(attrs={"class":"form-control searchable-select","id":"id_vendor"}),
            "payment_date":forms.DateInput(attrs={"type":"date","class":"form-control"}),
            "number":forms.TextInput(attrs={"class":"form-control"}),
            "payment_method":forms.TextInput(attrs={"class":"form-control"}),
            "payment_account":forms.Select(attrs={"class":"form-control"}),
            "accounts_payable_account":forms.Select(attrs={"class":"form-control"}),
            "currency":forms.TextInput(attrs={"class":"form-control"}),
            "memo":forms.Textarea(attrs={"class":"form-control","rows":2}),
        }
    def __init__(self,*args,**kwargs):
        company=kwargs.pop("company",None);super().__init__(*args,**kwargs)
        if company:
            self.fields["vendor"].queryset=Vendor.objects.filter(company=company,is_active=True).order_by("name")
            accounts=_company_accounts(company); self.fields["payment_account"].queryset=accounts; self.fields["accounts_payable_account"].queryset=accounts
            if not self.is_bound and not self.instance.pk:
                ap=find_default_ap_account(company); cash=(accounts.filter(name__icontains="cash").first() or accounts.filter(name__icontains="bank").first() or accounts.filter(account_type=ChartOfAccount.ACCOUNT_TYPE_ASSET).first())
                if ap:self.fields["accounts_payable_account"].initial=ap.pk
                if cash:self.fields["payment_account"].initial=cash.pk
        else:
            self.fields["vendor"].queryset=Vendor.objects.none();self.fields["payment_account"].queryset=ChartOfAccount.objects.none();self.fields["accounts_payable_account"].queryset=ChartOfAccount.objects.none()

class VendorPaymentAllocationForm(forms.ModelForm):
    class Meta:
        model=VendorPaymentAllocation; fields=["bill","discount","amount","memo"]
        widgets={"bill":forms.Select(attrs={"class":"form-control"}),"discount":forms.NumberInput(attrs={"class":"form-control","step":"0.01"}),"amount":forms.NumberInput(attrs={"class":"form-control","step":"0.01"}),"memo":forms.TextInput(attrs={"class":"form-control"})}
    def __init__(self,*args,**kwargs):
        company=kwargs.pop("company",None);vendor_id=kwargs.pop("vendor_id",None);super().__init__(*args,**kwargs)
        qs=PurchaseBill.objects.none()
        if company:
            qs=PurchaseBill.objects.filter(company=company,status=PurchaseBill.STATUS_POSTED)
            if vendor_id:qs=qs.filter(vendor_id=vendor_id)
        self.fields["bill"].queryset=qs.order_by("bill_date","id")

class VendorPaymentOtherChargeForm(forms.ModelForm):
    class Meta:
        model=VendorPaymentOtherCharge; fields=["memo","amount","account"]
        widgets={"memo":forms.TextInput(attrs={"class":"form-control"}),"amount":forms.NumberInput(attrs={"class":"form-control","step":"0.01"}),"account":forms.Select(attrs={"class":"form-control"})}
    def __init__(self,*args,**kwargs):
        company=kwargs.pop("company",None);super().__init__(*args,**kwargs);self.fields["account"].queryset=_company_accounts(company) if company else ChartOfAccount.objects.none()

VendorPaymentAllocationFormSet=inlineformset_factory(VendorPayment,VendorPaymentAllocation,form=VendorPaymentAllocationForm,extra=1,can_delete=True)
VendorPaymentOtherChargeFormSet=inlineformset_factory(VendorPayment,VendorPaymentOtherCharge,form=VendorPaymentOtherChargeForm,extra=1,can_delete=True)
