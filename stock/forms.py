from django import forms
from django.forms import inlineformset_factory

from accounting.models import ChartOfAccount
from .models import (
    Item,
    ItemBrand,
    ItemGroup,
    StockDocument,
    StockDocumentLine,
    UnitSet,
    Warehouse,
)


class ItemGroupForm(forms.ModelForm):
    class Meta:
        model = ItemGroup
        fields = ["name", "code", "memo", "is_active"]


class ItemBrandForm(forms.ModelForm):
    class Meta:
        model = ItemBrand
        fields = ["name", "description", "is_active"]


class UnitSetForm(forms.ModelForm):
    class Meta:
        model = UnitSet
        fields = ["name", "base_unit", "default_purchase", "default_sale", "memo", "is_active"]


class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ["name", "code", "memo", "is_active"]


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            "code",
            "name",
            "item_type",
            "item_group",
            "item_brand",
            "unit_set",
            "cost_price",
            "sale_price",
            "inventory_account",
            "cogs_account",
            "revenue_account",
            "memo",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields["item_group"].queryset = ItemGroup.objects.filter(
                company=company,
                is_active=True,
            ).order_by("name")

            self.fields["item_brand"].queryset = ItemBrand.objects.filter(
                company=company,
                is_active=True,
            ).order_by("name")

            self.fields["unit_set"].queryset = UnitSet.objects.filter(
                company=company,
                is_active=True,
            ).order_by("name")

            accounts = ChartOfAccount.objects.filter(
                company=company,
                is_active=True,
                is_group=False,
            ).order_by("code")

            self.fields["inventory_account"].queryset = accounts
            self.fields["cogs_account"].queryset = accounts
            self.fields["revenue_account"].queryset = accounts
        else:
            self.fields["item_group"].queryset = ItemGroup.objects.none()
            self.fields["item_brand"].queryset = ItemBrand.objects.none()
            self.fields["unit_set"].queryset = UnitSet.objects.none()
            self.fields["inventory_account"].queryset = ChartOfAccount.objects.none()
            self.fields["cogs_account"].queryset = ChartOfAccount.objects.none()
            self.fields["revenue_account"].queryset = ChartOfAccount.objects.none()


class StockDocumentForm(forms.ModelForm):
    class Meta:
        model = StockDocument
        fields = [
            "document_date",
            "number",
            "warehouse",
            "from_warehouse",
            "to_warehouse",
            "debit_account",
            "credit_account",
            "memo",
            "status",
        ]
        widgets = {
            "document_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)
        document_type = kwargs.pop("document_type", None)

        super().__init__(*args, **kwargs)

        if company:
            warehouses = Warehouse.objects.filter(
                company=company,
                is_active=True,
            ).order_by("name")

            self.fields["warehouse"].queryset = warehouses
            self.fields["from_warehouse"].queryset = warehouses
            self.fields["to_warehouse"].queryset = warehouses

            accounts = ChartOfAccount.objects.filter(
                company=company,
                is_active=True,
                is_group=False,
            ).order_by("code")

            self.fields["debit_account"].queryset = accounts
            self.fields["credit_account"].queryset = accounts
        else:
            self.fields["warehouse"].queryset = Warehouse.objects.none()
            self.fields["from_warehouse"].queryset = Warehouse.objects.none()
            self.fields["to_warehouse"].queryset = Warehouse.objects.none()
            self.fields["debit_account"].queryset = ChartOfAccount.objects.none()
            self.fields["credit_account"].queryset = ChartOfAccount.objects.none()

        if document_type == StockDocument.TYPE_TRANSFER:
            self.fields["debit_account"].required = False
            self.fields["credit_account"].required = False
            self.fields["warehouse"].required = False
            self.fields["from_warehouse"].required = True
            self.fields["to_warehouse"].required = True
        else:
            self.fields["warehouse"].required = True
            self.fields["from_warehouse"].required = False
            self.fields["to_warehouse"].required = False

        if document_type in [
            StockDocument.TYPE_ISSUE,
            StockDocument.TYPE_ADJUSTMENT,
            StockDocument.TYPE_ASSEMBLY,
        ]:
            self.fields["debit_account"].required = True
            self.fields["credit_account"].required = True


class StockDocumentLineForm(forms.ModelForm):
    class Meta:
        model = StockDocumentLine
        fields = ["item", "qty", "unit_cost", "memo"]

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields["item"].queryset = Item.objects.filter(
                company=company,
                is_active=True,
            ).order_by("code", "name")
        else:
            self.fields["item"].queryset = Item.objects.none()


StockDocumentLineFormSet = inlineformset_factory(
    StockDocument,
    StockDocumentLine,
    form=StockDocumentLineForm,
    extra=5,
    can_delete=True,
)