import json

from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from . import llm

LIMITE_PAR_MINUTE = 15


@staff_member_required
def chat(request):
    ctx = {**admin.site.each_context(request), "title": "Assistant IA",
           "ia_active": llm.ia_disponible(),
           "rapides": [(k, v[0]) for k, v in llm.QUESTIONS_RAPIDES.items()]}
    return render(request, "assistant/chat.html", ctx)


@staff_member_required
@require_POST
def poser_question(request):
    cle = f"assistant:{request.user.pk}"
    n = cache.get(cle, 0)
    if n >= LIMITE_PAR_MINUTE:
        return JsonResponse({"reponse": "Trop de questions en peu de temps : patientez une minute.", "source": "erreur"}, status=429)
    cache.set(cle, n + 1, 60)
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"reponse": "Requête invalide.", "source": "erreur"}, status=400)
    if data.get("rapide"):
        return JsonResponse(llm.question_rapide(str(data["rapide"])))
    historique = data.get("historique") if isinstance(data.get("historique"), list) else []
    return JsonResponse(llm.repondre(str(data.get("question", "")), historique))
