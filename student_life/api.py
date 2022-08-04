import json

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage
from django.db.models import OuterRef, QuerySet, Count, F
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.http.request import HttpRequest

from student_life.encoders import ClubEncoder, ClubMemberEncoder
from student_life.models import Club, ClubMember


def __convert_page_parameters(request: dict[str]) -> tuple:
    """
    Convertit les paramètres de la requête pour qu'ils soient utilisables par la fonction
    :func:`~student_life.api.get_clubs_filtered`.
    """
    try:
        page = int(request.get('page', [1])[0])
        page_size = int(request.get('page_size', [10])[0])
    except SyntaxError or ValueError:
        raise ValueError('Les paramètres de la page doivent être des entiers')
    if not 0 < page_size < 21:
        raise ValueError('La page doit contenir entre 1 et 20 éléments')
    if page < 1:
        raise ValueError('La page doit être supérieure à 0')
    return page, page_size


def __is_sort_field_valid(sort_field: str) -> bool:
    """
    Vérifie si le champ de tri passé en paramètre est valide.
    """
    valid_fields = ('name', 'created_at', 'members')
    sort_field = sort_field.removesuffix('-count').removeprefix('-')
    return sort_field in valid_fields


def __sort_queryset(queryset: QuerySet, sort_field: str) -> QuerySet:
    """
    Trie une requête de clubs en fonction du champ de tri passé en paramètre.
    """
    if sort_field in "-members":
        sort_field = sort_field.replace('members', 'nb_members')
        queryset = queryset.annotate(nb_members=Count('members')).order_by(sort_field)
    else:
        queryset = queryset.order_by(sort_field)
    return queryset


def __filter_queryset(queryset: QuerySet, filters: dict[str, str]) -> QuerySet:
    if 'name' in filters:
        queryset = queryset.filter(name__icontains=filters['name'][0])
    if 'members' in filters:
        queryset = queryset.filter(clubmember__user__username__icontains=filters['members'][0])
    if 'president' in filters:
        queryset = queryset.filter(president__icontains=filters['president'][0])
    return queryset


def get_clubs(request: HttpRequest) -> HttpResponse:
    """
    Renvoie une réponse JSON contenant les clubs de la base de données correspondant aux filtres passés
    dans la requête.
    Les filtres de la requête peuvent être les suivants :
        - name : nom du club
        - members : noms des membres du club
        - president : nom du président du club
        - page : numéro de la page (par défaut 1)
        - page_size : nombre d'éléments par page (par défaut 10)
        - sort_by : colonne sur laquelle trier (par défaut 'name')
    Si un filtre de la requête n'est pas conforme, la fonction renvoie une erreur HTTP 400.

    Le JSON de la réponse est formé de la manière suivante : ::

        {
            "model": "student_life.club",
            "id": <int>,
            "name": "Nom du club",
            "description": "Une très belle description",
            "logo": "path/to/img",
            "is_active": <bool>,
            "created_at": "2022-07-24T17:30:52.662Z",
            "president": "Nom du président"
        }
    """
    dict_req = dict(request.GET)
    valid_keys = ('name', 'members', 'page', 'page-size', 'order-by', 'president')
    if not all((key in valid_keys for key in dict_req.keys())):
        return HttpResponseBadRequest(f'Les paramètres acceptés sont : {", ".join(valid_keys)}')
    sort_field: str = dict_req.get('order-by', ['name'])[0]
    if not __is_sort_field_valid(sort_field):
        return HttpResponseBadRequest(f'Le champ de tri {sort_field} n\'est pas valide')
    queryset = Club.objects.annotate(
        president=ClubMember.objects.filter(club_id=OuterRef('id'), is_president=True).values('user__username')
    )
    queryset = __sort_queryset(queryset, sort_field)
    queryset = __filter_queryset(queryset, dict_req)
    try:
        page, page_size = __convert_page_parameters(dict_req)
    except ValueError as err:
        return HttpResponseBadRequest(str(err))
    try:
        paginator = Paginator(queryset, page_size)
        result = paginator.page(page)
    except EmptyPage:
        return HttpResponseBadRequest('La page demandée n\'existe pas')
    result = json.dumps(result, cls=ClubEncoder)
    return HttpResponse(result, content_type='application/json')


def get_club_members(request: HttpRequest, club_id: int) -> HttpResponse:
    """
    Renvoie une réponse JSON contenant les membres d'un club. La recherche du club se fait par son ID.
    Les membres sont triés par importance : d'abord le président, puis le bureau, puis les autres membres.

    Le JSON de la réponse est formé de la manière suivante : ::

        {
            'id': <int>,
            'user_id': <int>,
            'name': <str>,
            'club': <str>,
            'member_since': <DateTime>, # in ISO format
            'is_in_bureau': <bool>,
            'is_president': <bool>,
            'poste': <str>,
        }
    """
    if not request.user.is_authenticated:
        return HttpResponseForbidden('Vous devez être authentifié pour accéder à cette ressource')
    queryset = ClubMember.objects.filter(club_id=club_id) \
        .annotate(name=ClubMember.objects.values('user__username')) \
        .order_by(F('is_president').desc(), F('is_in_bureau').desc(), F('member_since').desc())
    response = json.dumps(list(queryset), cls=ClubMemberEncoder)
    return HttpResponse(response, content_type='application/json')
