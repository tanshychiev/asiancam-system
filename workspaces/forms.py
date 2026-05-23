from django import forms
from django.contrib.auth import get_user_model

from .models import MonthlyWorkspace

User = get_user_model()


class MonthlyWorkspaceForm(forms.ModelForm):
    assigned_staff = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = MonthlyWorkspace
        fields = [
            "client",
            "year",
            "month",
            "title",
            "assigned_staff",
            "status",
            "due_date",
            "note",
        ]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "note": forms.Textarea(attrs={"rows": 3}),
        }
