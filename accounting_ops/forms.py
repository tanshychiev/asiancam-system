from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone

from .models import ChartOfAccount, JournalEntry, JournalEntryLine


class ChartOfAccountForm(forms.ModelForm):
    class Meta:
        model = ChartOfAccount
        fields = [
            "code",
            "name",
            "local_name",
            "account_type",
            "report_type",
            "report_section",
            "normal_balance",
            "parent",
            "is_group",
            "is_active",
            "description",
        ]

        widgets = {
            "code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Example: 1010",
            }),
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Example: Cash on Hand",
            }),
            "local_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Khmer/local account name",
            }),
            "account_type": forms.Select(attrs={"class": "form-control"}),
            "report_type": forms.Select(attrs={"class": "form-control"}),
            "report_section": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Example: Current Asset",
            }),
            "normal_balance": forms.Select(attrs={"class": "form-control"}),
            "parent": forms.Select(attrs={"class": "form-control"}),
            "is_group": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Description or usage note",
            }),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

        if self.company:
            self.fields["parent"].queryset = ChartOfAccount.objects.filter(
                company=self.company,
                is_group=True,
                is_active=True,
            ).order_by("code")
        else:
            self.fields["parent"].queryset = ChartOfAccount.objects.none()

        self.fields["parent"].required = False
        self.fields["parent"].empty_label = "No parent account"

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip()

        qs = ChartOfAccount.objects.filter(
            company=self.company,
            code=code,
        )

        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("This account code already exists for this company.")

        return code

    def clean(self):
        cleaned_data = super().clean()

        account_type = cleaned_data.get("account_type")
        report_type = cleaned_data.get("report_type")

        balance_sheet_types = ["asset", "liability", "equity"]
        profit_loss_types = [
            "revenue",
            "cogs",
            "expense",
            "other_income",
            "other_expense",
        ]

        if account_type in balance_sheet_types and report_type != "balance_sheet":
            raise forms.ValidationError("Asset, Liability, and Equity accounts must map to Balance Sheet.")

        if account_type in profit_loss_types and report_type != "profit_loss":
            raise forms.ValidationError("Revenue and Expense accounts must map to Profit & Loss.")

        return cleaned_data


class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = [
            "entry_date",
            "reference_no",
            "description",
            "status",
        ]

        widgets = {
            "entry_date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control",
            }),
            "reference_no": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Reference no, invoice no, receipt no...",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Journal description",
            }),
            "status": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            self.fields["entry_date"].initial = timezone.localdate()
            self.fields["status"].initial = JournalEntry.STATUS_POSTED


class JournalEntryLineForm(forms.ModelForm):
    class Meta:
        model = JournalEntryLine
        fields = [
            "account",
            "description",
            "debit",
            "credit",
        ]

        widgets = {
            "account": forms.Select(attrs={
                "class": "form-control account-select",
            }),
            "description": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Line note",
            }),
            "debit": forms.NumberInput(attrs={
                "class": "form-control debit-input",
                "step": "0.01",
                "min": "0",
                "placeholder": "0.00",
            }),
            "credit": forms.NumberInput(attrs={
                "class": "form-control credit-input",
                "step": "0.01",
                "min": "0",
                "placeholder": "0.00",
            }),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields["account"].queryset = ChartOfAccount.objects.filter(
                company=company,
                is_active=True,
                is_group=False,
            ).order_by("code")
        else:
            self.fields["account"].queryset = ChartOfAccount.objects.none()

        self.fields["account"].empty_label = "Select account"


JournalEntryLineFormSet = inlineformset_factory(
    JournalEntry,
    JournalEntryLine,
    form=JournalEntryLineForm,
    extra=4,
    min_num=2,
    validate_min=True,
    can_delete=True,
)