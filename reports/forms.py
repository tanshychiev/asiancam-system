from django import forms
from .models import ReportFile


class ReportFileForm(forms.ModelForm):
    class Meta:
        model = ReportFile
        fields = ["workspace", "title", "file_type", "file", "visible_to_customer", "note"]
        widgets = {
            "note": forms.Textarea(attrs={"rows": 3}),
        }
