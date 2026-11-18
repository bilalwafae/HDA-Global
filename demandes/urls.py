from django.urls import path
from . import views

app_name = "demandes"

urlpatterns = [
    path("", views.create, name="create"),
    path("confirmation/<str:reference>/", views.confirmation, name="confirmation"),
]

