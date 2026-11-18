"""URLs pour le portail de suivi client (token UUID)."""
from django.urls import path
from . import views

app_name = "suivi"

urlpatterns = [
    path("<uuid:token>/", views.suivi, name="detail"),
]

