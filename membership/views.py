from django import forms
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as base_views, forms as base_forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Field, Submit


class LoginForm(base_forms.AuthenticationForm):
    helper = FormHelper()
    helper.layout = Layout(
        Fieldset(
            'Please sign in',
            'username',
            'password',
        ),
        Field('next', type='hidden'),
        Submit('submit', 'Sign in'),
    )
    next = forms.CharField(required=False)

    def __init__(self, request=None, *args, **kwargs):
        kwargs["initial"]["next"] = request.GET.get("next")
        super().__init__(request, *args, **kwargs)


class LoginView(base_views.LoginView):
    form_class = LoginForm
    template_name = "membership/login.html"


class LogoutView(base_views.LogoutView):
    pass


class PasswordChangeView(base_views.PasswordChangeView):
    pass


class PasswordChangeDoneView(base_views.PasswordChangeDoneView):
    pass


class PasswordResetView(base_views.PasswordResetView):
    pass


class PasswordResetDoneView(base_views.PasswordResetDoneView):
    pass


class PasswordResetConfirmView(base_views.PasswordResetConfirmView):
    pass


class PasswordResetCompleteView(base_views.PasswordResetCompleteView):
    pass


@login_required()
def account_view(request):
    return render(request, 'membership/account.html')
