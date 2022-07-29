from django.core.paginator import Paginator
from django.db.models import OuterRef
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render

from .models import Club, ClubMember


def view_all_clubs(request, page = 1) -> HttpResponse:
    res = Club.objects.order_by('name') \
        .values('id', 'name', 'description', 'logo', 'is_active', 'created_at', 'short_description') \
        .annotate(
        president=ClubMember.objects.filter(club_id=OuterRef('id'), is_president=True).values('user__username'))
    paginator = Paginator(res, 10)
    context = {
        'clubs': paginator.get_page(page),
        'nb_pages': paginator.num_pages,
        'page_indexes': paginator.page_range
    }
    return render(request, 'student_life/view_all.html', context)


def view_detail(request: HttpRequest, club_id: int, name) -> HttpResponse:
    """
    Renvoie la page contenant les détails sur un club

    :param request: la requête HTTP effectuée par le client
    :param club_id: la clef primaire du club à afficher
    :param name: le nom du club à afficher. Ce paramètre n'est pas utilisé.
    Son utilisation est juste pour que le paramètre `name` soit pris en compte dans l'URL
    :return: la page contenant les détails sur le club (code Http 200). Si aucun club ne correspond à l'id
    fourni, une erreur Http 404 est renvoyée
    """
    club = Club.objects.all().annotate(
        president=ClubMember.objects.filter(club_id=OuterRef('id'), is_president=True).values('user__username')
    )
    try:
        club = club.get(id=club_id)
    except Club.DoesNotExist:
        return HttpResponse(reason=f"Il n'existe aucun club avec l'id {club_id}", status=404)
    context = {'club': club}
    return render(request, 'student_life/view_detail.html', context)
