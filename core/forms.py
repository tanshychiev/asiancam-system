from django import forms
from django.contrib.auth.models import User, Group, Permission

from .models import Company, UserProfile


class StaffUserCreateForm(forms.ModelForm):
    USER_TYPE_CHOICES = [
        ("staff", "Staff User"),
        ("client", "Client User"),
    ]

    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        initial="staff",
        label="User Type",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    company = forms.ModelChoiceField(
        queryset=Company.objects.filter(is_active=True).order_by("name"),
        required=False,
        empty_label="Select company for client user",
        label="Client Company",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    role = forms.ModelChoiceField(
        queryset=Group.objects.all().order_by("name"),
        required=False,
        empty_label="Select staff role",
        label="Role",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    phone = forms.CharField(
        required=False,
        label="Phone",
        widget=forms.TextInput(attrs={
            "placeholder": "Phone number",
            "class": "form-control",
        }),
    )

    position = forms.CharField(
        required=False,
        label="Position",
        widget=forms.TextInput(attrs={
            "placeholder": "Position",
            "class": "form-control",
        }),
    )

    can_view_reports = forms.BooleanField(required=False, initial=True)
    can_download_reports = forms.BooleanField(required=False, initial=True)

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Password",
            "class": "form-control",
        }),
    )

    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Confirm password",
            "class": "form-control",
        }),
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active"]
        widgets = {
            "username": forms.TextInput(attrs={
                "placeholder": "Username",
                "class": "form-control",
            }),
            "first_name": forms.TextInput(attrs={
                "placeholder": "First name",
                "class": "form-control",
            }),
            "last_name": forms.TextInput(attrs={
                "placeholder": "Last name",
                "class": "form-control",
            }),
            "email": forms.EmailInput(attrs={
                "placeholder": "Email",
                "class": "form-control",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def clean_username(self):
        username = self.cleaned_data.get("username")

        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username already exists.")

        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email already exists.")

        return email

    def clean(self):
        cleaned_data = super().clean()

        user_type = cleaned_data.get("user_type")
        company = cleaned_data.get("company")
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Password and confirm password do not match.")

        if user_type == "client" and not company:
            raise forms.ValidationError("Client user must select a company.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        user_type = self.cleaned_data.get("user_type")
        role = self.cleaned_data.get("role")
        password = self.cleaned_data.get("password")

        user.set_password(password)

        if user_type == "staff" and role and role.name.lower() == "admin":
            user.is_staff = True
        else:
            user.is_staff = False

        if commit:
            user.save()

            if user_type == "staff" and role:
                user.groups.add(role)

            UserProfile.objects.create(
                user=user,
                user_type=user_type,
                company=self.cleaned_data.get("company") if user_type == "client" else None,
                phone=self.cleaned_data.get("phone") or "",
                position=self.cleaned_data.get("position") or "",
                can_view_reports=self.cleaned_data.get("can_view_reports"),
                can_download_reports=self.cleaned_data.get("can_download_reports"),
            )

        return user


class StaffUserEditForm(forms.ModelForm):
    user_type = forms.ChoiceField(
        choices=UserProfile.USER_TYPE_CHOICES,
        label="User Type",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    company = forms.ModelChoiceField(
        queryset=Company.objects.filter(is_active=True).order_by("name"),
        required=False,
        empty_label="Select company for client user",
        label="Client Company",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    role = forms.ModelChoiceField(
        queryset=Group.objects.all().order_by("name"),
        required=False,
        empty_label="Select staff role",
        label="Role",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": "Phone number",
            "class": "form-control",
        }),
    )

    position = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": "Position",
            "class": "form-control",
        }),
    )

    can_view_reports = forms.BooleanField(required=False)
    can_download_reports = forms.BooleanField(required=False)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active"]
        widgets = {
            "username": forms.TextInput(attrs={
                "placeholder": "Username",
                "class": "form-control",
            }),
            "first_name": forms.TextInput(attrs={
                "placeholder": "First name",
                "class": "form-control",
            }),
            "last_name": forms.TextInput(attrs={
                "placeholder": "Last name",
                "class": "form-control",
            }),
            "email": forms.EmailInput(attrs={
                "placeholder": "Email",
                "class": "form-control",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        profile, created = UserProfile.objects.get_or_create(
            user=self.instance,
            defaults={"user_type": "staff"},
        )

        self.fields["user_type"].initial = profile.user_type
        self.fields["company"].initial = profile.company
        self.fields["phone"].initial = profile.phone
        self.fields["position"].initial = profile.position
        self.fields["can_view_reports"].initial = profile.can_view_reports
        self.fields["can_download_reports"].initial = profile.can_download_reports

        first_group = self.instance.groups.first()

        if first_group:
            self.fields["role"].initial = first_group

    def clean_username(self):
        username = self.cleaned_data.get("username")

        if username:
            exists = User.objects.filter(username=username).exclude(id=self.instance.id).exists()

            if exists:
                raise forms.ValidationError("This username already exists.")

        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if email:
            exists = User.objects.filter(email=email).exclude(id=self.instance.id).exists()

            if exists:
                raise forms.ValidationError("This email already exists.")

        return email

    def clean(self):
        cleaned_data = super().clean()

        user_type = cleaned_data.get("user_type")
        company = cleaned_data.get("company")

        if user_type == "client" and not company:
            raise forms.ValidationError("Client user must select a company.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        user_type = self.cleaned_data.get("user_type")
        role = self.cleaned_data.get("role")

        if user_type == "staff" and role and role.name.lower() == "admin":
            user.is_staff = True
        elif not user.is_superuser:
            user.is_staff = False

        if commit:
            user.save()

            if not user.is_superuser:
                user.groups.clear()

                if user_type == "staff" and role:
                    user.groups.add(role)

            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={"user_type": user_type},
            )

            profile.user_type = user_type
            profile.company = self.cleaned_data.get("company") if user_type == "client" else None
            profile.phone = self.cleaned_data.get("phone") or ""
            profile.position = self.cleaned_data.get("position") or ""
            profile.can_view_reports = self.cleaned_data.get("can_view_reports")
            profile.can_download_reports = self.cleaned_data.get("can_download_reports")
            profile.save()

        return user


class StaffPasswordChangeForm(forms.Form):
    password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            "placeholder": "New password",
            "class": "form-control",
        }),
    )

    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Confirm password",
            "class": "form-control",
        }),
    )

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Password and confirm password do not match.")

        if password and len(password) < 6:
            raise forms.ValidationError("Password must be at least 6 characters.")

        return cleaned_data


class CompanyCreateForm(forms.ModelForm):
    assigned_staff = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(
            is_active=True,
            is_superuser=False,
        ).order_by("username"),
        required=False,
        label="Assigned Staff",
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Company
        fields = [
            "name",
            "code",
            "logo",
            "vatin",
            "phone",
            "email",
            "address",
            "assigned_staff",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "Company name",
                "class": "form-control",
            }),
            "code": forms.TextInput(attrs={
                "placeholder": "Company code",
                "class": "form-control",
            }),
            "logo": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
                "id": "id_logo",
            }),
            "vatin": forms.TextInput(attrs={
                "placeholder": "VATIN / Tax ID",
                "class": "form-control",
            }),
            "phone": forms.TextInput(attrs={
                "placeholder": "Phone number",
                "class": "form-control",
            }),
            "email": forms.EmailInput(attrs={
                "placeholder": "Email",
                "class": "form-control",
            }),
            "address": forms.Textarea(attrs={
                "placeholder": "Address",
                "rows": 4,
                "class": "form-control",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }


class AssignStaffForm(forms.Form):
    company = forms.ModelChoiceField(
        queryset=Company.objects.filter(is_active=True).order_by("name"),
        label="Company",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    staff = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_superuser=False, is_active=True).order_by("username"),
        label="Staff",
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class RoleCreateForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all().order_by(
            "content_type__app_label",
            "content_type__model",
            "codename",
        ),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Permissions",
    )

    class Meta:
        model = Group
        fields = ["name", "permissions"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Role name, example: Accountant",
                    "class": "form-control",
                }
            ),
        }