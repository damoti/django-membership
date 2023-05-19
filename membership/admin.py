from django import forms
from django.core.exceptions import ValidationError
from django.contrib import admin
from django.contrib.auth import password_validation
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, EmailTemplate


admin.site.unregister(Group)


class UserCreationForm(forms.ModelForm):
    error_messages = {
        "password_mismatch": _("The two password fields didn’t match."),
        "unique": _("A user with that username already exists."),
    }
    password1 = forms.CharField(
        label=_("Password"),
        strip=False, required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False, required=False,
        help_text=_("Enter the same password as before, for verification."),
    )
    generate_password = forms.BooleanField(
        label=_("Generate Password"),
        initial=True, required=False,
        help_text=_("Generate and email password to the user."),
    )
    send_welcome_email = forms.BooleanField(
        label=_("Send Welcome Email"),
        initial=True, required=False,
        help_text=_("Send welcome email with users password."),
    )

    class Meta:
        model = User
        fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs["autofocus"] = True

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("generate_password", False):
            for password in ("password1", "password2"):
                if not cleaned_data.get(password):
                    self.add_error(
                        password, ValidationError(
                            self.fields[password].error_messages["required"], code="required"
                        )
                    )
        return cleaned_data

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                self.error_messages["password_mismatch"],
                code="password_mismatch",
            )
        return password2

    def _post_clean(self):
        super()._post_clean()
        # Validate the password after self.instance is updated with form data
        # by super().
        password = self.cleaned_data.get("password2")
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except ValidationError as error:
                self.add_error("password2", error)

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data["generate_password"]:
            raw_password = User.objects.generate_password()
        else:
            raw_password = self.cleaned_data["password1"]
        email = self.cleaned_data["email"]
        user.set_username(email[:email.index('@')])
        user.set_password(raw_password)
        if commit:
            user.save()
            if hasattr(self, "save_m2m"):
                self.save_m2m()
        if self.cleaned_data["send_welcome_email"]:
            user.send_welcome_email(raw_password)
        return user


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = BaseUserAdmin.list_display + ('last_login',)
    fieldsets = BaseUserAdmin.fieldsets
    add_form = UserCreationForm
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email", "first_name", "last_name",
                    "password1", "password2", "generate_password",
                    "send_welcome_email"
                ),
            },
        ),
    )

    @admin.action(description='Reset user password.')
    def reset_password(self, request, queryset):
        for user in queryset:
            password = User.objects.generate_password()
            user.set_password(password)
            user.send_welcome_email(password)
            user.save()

    actions = ['reset_password']


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    pass
