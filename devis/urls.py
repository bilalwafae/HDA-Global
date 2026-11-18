from django.urls import path
from . import views

app_name = "devis"

urlpatterns = [
    path("creer/<int:demande_id>/", views.creer_devis, name="creer"),
    path("auto/<int:demande_id>/", views.generer_auto, name="auto"),
    path("<int:pk>/editer/", views.editer_devis, name="editer"),
    path("suivi/<uuid:token>/<int:pk>/pdf/", views.telecharger_pdf, name="pdf"),
    path("suivi/<uuid:token>/<int:pk>/action/", views.action_client, name="action_client"),
]

