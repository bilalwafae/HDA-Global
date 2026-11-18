from django.urls import path
from . import views

app_name = "interventions"

urlpatterns = [
    path("planning/", views.planning, name="planning"),
]

