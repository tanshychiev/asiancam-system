from django import forms
from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            "company_name",
            "client_code",
            "tax_id",
            "industry",
            "contact_name",
            "contact_phone",
            "contact_email",
            "address",
            "customer_user",
            "status",
            "note",
        ]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
            "note": forms.Textarea(attrs={"rows": 3}),
        }
