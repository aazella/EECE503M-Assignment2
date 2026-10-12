"""Additional JSON endpoints for the mobile client and integrations."""

import json

from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from helpdesk.models import Ticket

User = get_user_model()


def _require_login(request):
    return request.user.is_authenticated


def user_detail(request, uid):
    """Return a user's profile."""
    if not _require_login(request):
        return JsonResponse({"detail": "authentication required"}, status=401)

    user = User.objects.filter(pk=uid).first()
    if not user:
        return JsonResponse({"detail": "not found"}, status=404)

    return JsonResponse(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "last_login": str(user.last_login),
            "password": user.password,
        }
    )


@csrf_exempt
def profile_update(request):
    """Update your own profile from a JSON body."""
    if not _require_login(request):
        return JsonResponse({"detail": "authentication required"}, status=401)
    if request.method != "POST":
        return JsonResponse({"detail": "POST required"}, status=405)

    data = json.loads(request.body or "{}")
    user = request.user
    for field, value in data.items():
        setattr(user, field, value)
    user.save()
    return JsonResponse(
        {"id": user.id, "username": user.username, "is_superuser": user.is_superuser}
    )


@csrf_exempt
def purge_closed(request):
    """Delete every closed ticket. Housekeeping for administrators."""
    if not _require_login(request):
        return JsonResponse({"detail": "authentication required"}, status=401)

    count = Ticket.objects.filter(status=Ticket.CLOSED_STATUS).count()
    Ticket.objects.filter(status=Ticket.CLOSED_STATUS).delete()
    return JsonResponse({"deleted": count})


def bulk_export(request):
    """Export up to `count` tickets in one call."""
    if not _require_login(request):
        return JsonResponse({"detail": "authentication required"}, status=401)

    count = int(request.GET.get("count", 100))
    base = list(
        Ticket.objects.values("id", "title", "submitter_email", "description")
    )
    rows = []
    while len(rows) < count:
        rows.extend(base)
    return JsonResponse({"count": len(rows[:count]), "tickets": rows[:count]})
