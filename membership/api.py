from django.contrib import auth
from ninja import NinjaAPI, Schema
from ninja.errors import ValidationError
from .auth import BearerAuthNinja, create_token


api = NinjaAPI(auth=BearerAuthNinja(), urls_namespace="membership")


class LoginDetails(Schema):
    username: str
    password: str


class TokenResponse(Schema):
    token: str


@api.post("/login", auth=None, response=TokenResponse)
def login(request, form: LoginDetails):
    user = auth.authenticate(
        request=request,
        username=form.username,
        password=form.password
    )
    if not user or not user.is_active:
        raise ValidationError([{"msg": "Invalid credentials."}])
    return {"token": create_token(user)}


class UserDetailsResponse(Schema):
    username: str


@api.get("/account", response=UserDetailsResponse)
def account_view(request):
    return request.user
