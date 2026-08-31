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
# =========================================================
# CUSTOMER REQUIREMENT FORMS
# =========================================================
from django.forms import inlineformset_factory
from stock.models import Item
from .models import SalesInvoice, SalesInvoiceLine, CustomerReceipt, CustomerReceiptAllocation, CustomerReceiptOtherCharge


def _active_accounts(company):
    if not company:
        return ChartOfAccount.objects.none()
    return ChartOfAccount.objects.filter(company=company, is_active=True, is_group=False).order_by("code", "name")


def find_default_ar_account(company):
    qs = _active_accounts(company)
    return (qs.filter(name__icontains="accounts receivable").first()
            or qs.filter(name__icontains="account receivable").first()
            or qs.filter(account_type=ChartOfAccount.ACCOUNT_TYPE_ASSET).first())


def find_default_cash_account(company):
    qs = _active_accounts(company)
    return (qs.filter(name__icontains="cash").first()
            or qs.filter(name__icontains="bank").first()
            or qs.filter(account_type=ChartOfAccount.ACCOUNT_TYPE_ASSET).first())


class SalesInvoiceForm(forms.ModelForm):
    class Meta:
        model = SalesInvoice
        fields = ["customer", "invoice_date", "due_date", "number", "po_number", "currency", "exchange_rate",
                  "accounts_receivable_account", "deposit_account", "salesperson", "memo"]
        widgets = {
            "customer": forms.Select(attrs={"class":"form-control searchable-select"}),
            "invoice_date": forms.DateInput(attrs={"type":"date","class":"form-control"}),
            "due_date": forms.DateInput(attrs={"type":"date","class":"form-control"}),
            "number": forms.TextInput(attrs={"class":"form-control"}),
            "po_number": forms.TextInput(attrs={"class":"form-control"}),
            "currency": forms.TextInput(attrs={"class":"form-control"}),
            "exchange_rate": forms.NumberInput(attrs={"class":"form-control","step":"0.0001"}),
            "accounts_receivable_account": forms.Select(attrs={"class":"form-control"}),
            "deposit_account": forms.Select(attrs={"class":"form-control"}),
            "salesperson": forms.Select(attrs={"class":"form-control"}),
            "memo": forms.Textarea(attrs={"class":"form-control","rows":2}),
        }
    def __init__(self,*args,**kwargs):
        self.company=kwargs.pop("company",None); self.document_type=kwargs.pop("document_type",SalesInvoice.TYPE_INVOICE)
        super().__init__(*args,**kwargs)
        if self.company:
            self.fields["customer"].queryset=Customer.objects.filter(company=self.company,is_active=True).order_by("name")
            self.fields["salesperson"].queryset=Salesperson.objects.filter(company=self.company,is_active=True).order_by("name")
            accounts=_active_accounts(self.company)
            self.fields["accounts_receivable_account"].queryset=accounts
            self.fields["deposit_account"].queryset=accounts
            if not self.is_bound and not self.instance.pk:
                ar=find_default_ar_account(self.company); cash=find_default_cash_account(self.company)
                if ar: self.fields["accounts_receivable_account"].initial=ar.pk
                if cash: self.fields["deposit_account"].initial=cash.pk
        else:
            self.fields["customer"].queryset=Customer.objects.none(); self.fields["salesperson"].queryset=Salesperson.objects.none()
            self.fields["accounts_receivable_account"].queryset=ChartOfAccount.objects.none(); self.fields["deposit_account"].queryset=ChartOfAccount.objects.none()
        self.fields["deposit_account"].required = self.document_type == SalesInvoice.TYPE_SALE_RECEIPT


class SalesInvoiceLineForm(forms.ModelForm):
    class Meta:
        model=SalesInvoiceLine
        fields=["item","description","qty","unit_name","unit_price","discount_amount","revenue_account","tax_amount"]
        widgets={
            "item":forms.Select(attrs={"class":"form-control js-sale-item"}),
            "description":forms.TextInput(attrs={"class":"form-control"}),
            "qty":forms.NumberInput(attrs={"class":"form-control js-qty","step":"0.01","min":"0"}),
            "unit_name":forms.TextInput(attrs={"class":"form-control"}),
            "unit_price":forms.NumberInput(attrs={"class":"form-control js-price","step":"0.01","min":"0"}),
            "discount_amount":forms.NumberInput(attrs={"class":"form-control js-discount","step":"0.01","min":"0"}),
            "revenue_account":forms.Select(attrs={"class":"form-control"}),
            "tax_amount":forms.NumberInput(attrs={"class":"form-control js-tax","step":"0.01","min":"0"}),
        }
    def __init__(self,*args,**kwargs):
        company=kwargs.pop("company",None); super().__init__(*args,**kwargs)
        if company:
            self.fields["item"].queryset=Item.objects.filter(company=company,is_active=True).select_related("unit_set","revenue_account").order_by("code","name")
            self.fields["revenue_account"].queryset=_active_accounts(company)
        else:
            self.fields["item"].queryset=Item.objects.none(); self.fields["revenue_account"].queryset=ChartOfAccount.objects.none()

SalesInvoiceLineFormSet=inlineformset_factory(SalesInvoice,SalesInvoiceLine,form=SalesInvoiceLineForm,extra=1,can_delete=True,min_num=1,validate_min=True)


class CustomerReceiptForm(forms.ModelForm):
    class Meta:
        model=CustomerReceipt
        fields=["customer","receipt_date","number","payment_method","deposit_account","currency","memo"]
        widgets={
            "customer":forms.Select(attrs={"class":"form-control searchable-select","id":"id_customer"}),
            "receipt_date":forms.DateInput(attrs={"type":"date","class":"form-control"}),
            "number":forms.TextInput(attrs={"class":"form-control"}),
            "payment_method":forms.TextInput(attrs={"class":"form-control"}),
            "deposit_account":forms.Select(attrs={"class":"form-control"}),
            "currency":forms.TextInput(attrs={"class":"form-control"}),
            "memo":forms.Textarea(attrs={"class":"form-control","rows":2}),
        }
    def __init__(self,*args,**kwargs):
        company=kwargs.pop("company",None); super().__init__(*args,**kwargs)
        if company:
            self.fields["customer"].queryset=Customer.objects.filter(company=company,is_active=True).order_by("name")
            self.fields["deposit_account"].queryset=_active_accounts(company)
            if not self.is_bound and not self.instance.pk:
                cash=find_default_cash_account(company)
                if cash:self.fields["deposit_account"].initial=cash.pk
        else:
            self.fields["customer"].queryset=Customer.objects.none(); self.fields["deposit_account"].queryset=ChartOfAccount.objects.none()


class CustomerReceiptAllocationForm(forms.ModelForm):
    class Meta:
        model=CustomerReceiptAllocation
        fields=["invoice","discount","amount","memo"]
        widgets={"invoice":forms.Select(attrs={"class":"form-control"}),"discount":forms.NumberInput(attrs={"class":"form-control","step":"0.01"}),"amount":forms.NumberInput(attrs={"class":"form-control","step":"0.01"}),"memo":forms.TextInput(attrs={"class":"form-control"})}
    def __init__(self,*args,**kwargs):
        company=kwargs.pop("company",None); customer_id=kwargs.pop("customer_id",None); super().__init__(*args,**kwargs)
        qs=SalesInvoice.objects.none()
        if company:
            qs=SalesInvoice.objects.filter(company=company,document_type=SalesInvoice.TYPE_INVOICE,status=SalesInvoice.STATUS_POSTED).select_related("customer")
            if customer_id: qs=qs.filter(customer_id=customer_id)
        self.fields["invoice"].queryset=qs.order_by("invoice_date","id")


class CustomerReceiptOtherChargeForm(forms.ModelForm):
    class Meta:
        model=CustomerReceiptOtherCharge
        fields=["memo","amount","account"]
        widgets={"memo":forms.TextInput(attrs={"class":"form-control"}),"amount":forms.NumberInput(attrs={"class":"form-control","step":"0.01"}),"account":forms.Select(attrs={"class":"form-control"})}
    def __init__(self,*args,**kwargs):
        company=kwargs.pop("company",None);super().__init__(*args,**kwargs);self.fields["account"].queryset=_active_accounts(company) if company else ChartOfAccount.objects.none()

CustomerReceiptAllocationFormSet=inlineformset_factory(CustomerReceipt,CustomerReceiptAllocation,form=CustomerReceiptAllocationForm,extra=1,can_delete=True)
CustomerReceiptOtherChargeFormSet=inlineformset_factory(CustomerReceipt,CustomerReceiptOtherCharge,form=CustomerReceiptOtherChargeForm,extra=1,can_delete=True)
