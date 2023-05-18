import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from ninja.security import HttpBearer as BaseNinjaHttpBearer


HS256 = "HS256"


def create_token(user):
    claims = {
        "id": user.id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(days=30),
    }
    return jwt.encode(
        claims, settings.SECRET_KEY, algorithm=HS256
    )


def read_token(token):
    claims = jwt.decode(
        token, settings.SECRET_KEY, algorithms=[HS256]
    )
    return claims["id"]


class BearerAuthNinja(BaseNinjaHttpBearer):
    def authenticate(self, request, token):
        user_id = read_token(token)
        request.user = get_user_model().objects.get(id=user_id)
        return True


class BearerAuthChannelsMiddleware:

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if not scope["user"].is_authenticated:
            for header in scope["headers"]:
                if header[0] in (b"Authorization", b"authorization"):
                    token = header[1][len('Bearer '):]
                    user_id = read_token(token)
                    scope["user"] = await get_user_model().objects.aget(id=user_id)
                    break
        return await self.inner(scope, receive, send)
