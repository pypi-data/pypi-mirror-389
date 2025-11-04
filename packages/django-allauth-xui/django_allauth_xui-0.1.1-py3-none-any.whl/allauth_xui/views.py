"""XUI Views"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic


class ProfileView(LoginRequiredMixin, generic.TemplateView):
    """User Profile view"""

    template_name = "allauth_xui/profile.html"
