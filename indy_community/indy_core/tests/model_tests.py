from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.views.generic.edit import UpdateView

from ..models import *


User = get_user_model()
TEST_USER_EMAIL = 'test@example.com'
TEST_USER_FIRST_NAME = 'Test'
TEST_USER_LAST_NAME = 'User'


class IndyUserTests(TestCase):
    """
    Tests for Indy custom User class.
    """

    def setUp(self):
        # Creates a single-user test database.
        self.user = User.objects.create(
            email=TEST_USER_EMAIL,
            first_name=TEST_USER_FIRST_NAME,
            last_name=TEST_USER_LAST_NAME,
        )

    def test_user_exists(self):
        # Tests user in setUp() does exists
        my_user = User.objects.filter(email=TEST_USER_EMAIL).all()[0]
        self.assertEqual(my_user.first_name, TEST_USER_FIRST_NAME)
