"""*Auth UI URLConf"""

from django.urls import path

from allauth_xui import views

urlpatterns = [
    path("profile/", views.ProfileView.as_view(), name="account_profile"),
]
