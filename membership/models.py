from django.db import models
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator


DEFAULT_RANDOM_PASSWORD_CHARS = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class UserManager(BaseUserManager):

    def get_by_natural_key(self, username):
        if '@' in username:
            return self.get(email=username)
        else:
            return self.get(username=username)

    def _create_user(self, email, password, **extra_fields):
        assert '@' in email
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_username(email[:email.index('@')])
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)

    @staticmethod
    def generate_password(length=8, allowed_chars=DEFAULT_RANDOM_PASSWORD_CHARS):
        return get_random_string(length, allowed_chars)


class User(AbstractBaseUser, PermissionsMixin):

    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        "username",
        max_length=150,
        unique=True,
        help_text=(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator],
        error_messages={
            "unique": "A user with that username already exists.",
        },
    )
    first_name = models.CharField("first name", max_length=150, blank=True)
    last_name = models.CharField("last name", max_length=150, blank=True)
    email = models.EmailField("email address", unique=True)
    is_staff = models.BooleanField(
        "staff status",
        default=False,
        help_text="Designates whether the user can log into this admin site.",
    )
    is_active = models.BooleanField(
        "active",
        default=True,
        help_text=(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField("date joined", default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def clean(self):
        super().clean()
        self.email = UserManager.normalize_email(self.email)

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    def set_username(self, username):
        _username = username
        for i in range(2, 1000):
            if not User.objects.filter(username=username).exists():
                self.username = username
                return username
            username = f"{_username}{i}"
        raise ValueError(f"Exhausted attempts to create a unique username from {_username}.")

    def send_welcome_email(self, password):
        EmailTemplate.objects.get_welcome_email().send_to(
            self, password=password
        )


class SystemEmail(models.Model):
    name = models.CharField(max_length=256)
    text = models.TextField()
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="emails")
    sent_on = models.DateTimeField(auto_now_add=True)


class EmailTemplateManager(models.Manager):
    WELCOME_EMAIL_NAME = "welcome-email"

    def get_welcome_email(self):
        return self.get(name=self.WELCOME_EMAIL_NAME)


class EmailTemplate(models.Model):
    name = models.CharField(max_length=256, unique=True)
    subject = models.CharField(max_length=256)
    body = models.TextField()

    objects = EmailTemplateManager()

    def send_to(self, user, **kwargs):
        send_mail(
            self.subject.format(user=user, **kwargs),
            self.body.format(user=user, **kwargs),
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
