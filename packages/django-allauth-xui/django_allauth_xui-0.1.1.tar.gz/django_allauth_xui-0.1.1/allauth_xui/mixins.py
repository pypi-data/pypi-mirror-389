"""*Auth UI Views"""

from django.contrib.auth.mixins import UserPassesTestMixin


class AccountOwnerMixin(UserPassesTestMixin):
    """Check if the user is owner of the account"""

    def test_func(self) -> bool | None:
        return self.request.user == self.get_object()
