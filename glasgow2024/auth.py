from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import AbstractBaseUser
from django.db.models import Q
from django.http import HttpRequest

UserModel = get_user_model()


# NOTE: This is not a fully functional backend, as it doesn't do membership
# checks and ignores the nominating member related object.
class GlasgowMemberAuthBackend(ModelBackend):
    def authenticate(
        self,
        request: HttpRequest | None,
        username: str | None = None,
        email: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> AbstractBaseUser | None:
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)

        if email is None:
            email = kwargs.get(UserModel.EMAIL_FIELD)

        if username is None or password is None:
            return
        try:
            user = UserModel.objects.get(Q(username=username) & Q(email=email))
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            UserModel().set_password(password)

        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
