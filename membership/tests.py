from textwrap import dedent
from django.test import TestCase
from django.core import mail
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService

from .models import User, EmailTemplate


class BaseTestCase(TestCase):

    def setUp(self):
        super().setUp()
        self.extra = {}
        self.user = User.objects.create_user(
            email='lex@damoti.com', password='pass',
        )

    async def apost(self, *args, **kwargs):
        return await self.async_client.post(
            *args, **kwargs, **self.extra
        )

    async def aget(self, *args, **kwargs):
        return await self.async_client.get(
            *args, **kwargs, **self.extra
        )


class APITests(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.extra["content_type"] = "application/json"

    async def login(self, username, password):
        response = await self.apost(
            '/api/login', data={'username': username, 'password': password}
        )
        json = response.json()
        token = json.get("token")
        if token is not None:
            self.extra["authorization"] = f"Bearer {token}"
        else:
            self.extra.pop("authorization", None)
        return response.status_code, json

    async def test_login(self):
        # incorrect password
        status_code, json = await self.login("lex", "wrong-pass")
        self.assertEqual(status_code, 422)
        self.assertEqual(json, {"detail": [{"msg": "Invalid credentials."}]})
        self.assertNotIn("authorization", self.extra)

        # unauthorized
        response = await self.aget("/api/account")
        self.assertEqual(response.status_code, 401)

        # successful login
        status_code, json = await self.login("lex", "pass")
        self.assertEqual(status_code, 200)
        self.assertIsNotNone(self.extra["authorization"])

        # authorized
        response = await self.aget("/api/account")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"username": "lex"})


class ViewTests(BaseTestCase):

    def assertInResponse(self, needle, response):
        self.assertIn(needle, response.content.decode())

    def assertHasInput(self, field_type, field_name, response, value=None):
        field = f'<input type="{field_type}" name="{field_name}"'
        if value is not None:
            field += f' value="{value}"'
        self.assertInResponse(field, response)

    def test_login_flow(self):
        # accessing protected page redirects to /login
        response = self.client.get("/account")
        self.assertRedirects(response, "/login?next=/account")

        # shows login form
        response = self.client.get("/login", {"next": "/account"})
        self.assertHasInput("text", "username", response)
        self.assertHasInput("password", "password", response)
        self.assertHasInput("hidden", "next", response, value="/account")

        # incorrect login
        response = self.client.post("/login", {"username": "lex", "password": "wrong-pass"})
        self.assertInResponse("Please enter a correct email address and password.", response)

        # valid login using username
        response = self.client.post("/login", {"username": "lex", "password": "pass", "next": "/account"})
        self.assertRedirects(response, "/account")

        # logout
        response = self.client.post("/logout")
        self.assertRedirects(response, "/login")
        # accessing protected page redirects to /login
        response = self.client.get("/account")
        self.assertRedirects(response, "/login?next=/account")

        # valid login using email instead of username
        response = self.client.post("/login", {"username": "lex@damoti.com", "password": "pass", "next": "/account"})
        self.assertRedirects(response, "/account")

        # account page works now
        response = self.client.get("/account")
        self.assertInResponse("lex@damoti.com", response)

    def test_admin(self):
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        self.client.post("/admin/login/", {"username": "lex", "password": "pass"})

        response = self.client.get("/admin/membership/user/")
        self.assertInResponse("lex@damoti.com", response)

        response = self.client.post("/admin/membership/user/add/", {"email": "lex@berezhny.com"})
        self.assertInResponse("This field is required.", response)

        EmailTemplate.objects.create(
            name=EmailTemplate.objects.WELCOME_EMAIL_NAME,
            subject="Welcome to membership app!",
            body=dedent("""\
            {user.first_name} {user.last_name},
            username: {user.email}
            password: {password}
            """)
        )

        response = self.client.post("/admin/membership/user/add/", {
            "email": "lex@berezhny.com", "send_welcome_email": True,
            "password1": "FooPass123", "password2": "FooPass123",
            "first_name": "Lex", "last_name": "Berezhny",
        })
        self.assertRedirects(response, "/admin/membership/user/2/change/")
        email = mail.outbox[0]
        self.assertEqual(email.subject, "Welcome to membership app!")
        self.assertEqual(
            email.body, "Lex Berezhny,\nusername: lex@berezhny.com\npassword: FooPass123\n"
        )


class SeleniumTests(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        service = ChromeService(executable_path=ChromeDriverManager().install())
        cls.selenium = webdriver.Chrome(service=service)
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_login(self):
        User.objects.create_user(
            email='lex@damoti.com', password='pass',
        )
        self.selenium.get('%s%s' % (self.live_server_url, '/login'))
        username_input = self.selenium.find_element(By.NAME, "username")
        username_input.send_keys('lex')
        password_input = self.selenium.find_element(By.NAME, "password")
        password_input.send_keys('pass')
        self.selenium.find_element(By.XPATH, '//input[@value="Sign in"]').click()
        self.selenium.get('%s%s' % (self.live_server_url, '/account'))
