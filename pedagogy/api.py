import json
import mimetypes
from datetime import datetime

import requests
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpRequest
from django.views.decorators.http import require_POST, require_GET
from django.core import serializers

from .forms import ReviewForm, UVSearchForm
from .models import Branch, Filiere, UV, Annal, Review


@login_required
@user_passes_test(lambda u: u.is_superuser)
def reset_categories(request: HttpRequest) -> HttpResponse:
    current_year = datetime.now().year
    url = f"https://extranet1.utbm.fr/gpedago/api/guide/formations/fr/{current_year}"
    categories = requests.get(url).json()
    codes = [c['code'] for c in categories]
    to_delete = Branch.objects.exclude(code__in=codes)  # on supprime les catégories qui n'existent plus
    try:
        to_delete.delete()
    except Exception as e:
        print(e)
    for category in categories:
        cat, _ = Branch.objects.get_or_create(code=category['code'])
        cat.name = category['libelle']
        cat.save()
    return HttpResponse('OK', status=200)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def reset_filieres(request: HttpRequest) -> HttpResponse:
    current_year = datetime.now().year
    url = f"https://extranet1.utbm.fr/gpedago/api/guide/filieres/fr/{current_year}"
    filieres = requests.get(url).json()
    codes = [c['code'] for c in filieres]
    to_delete = Filiere.objects.exclude(code__in=codes)  # on supprime les catégories qui n'existent plus
    if to_delete.exists():
        to_delete.delete()

    for filiere in filieres:
        try:
            branch = Branch.objects.get(code=filiere['codeFormation'])
        except Branch.DoesNotExist:
            msg = f'La filière {filiere["codeFormation"]} n\'existe pas. Réinitialisez les filières puis réessayez'
            return HttpResponse(msg, status=409)
        try:
            new = Filiere.objects.get(code=filiere['code'])
            new.name = filiere['libelle']
            new.branch = branch
            new.save()
        except Filiere.DoesNotExist:
            Filiere(code=filiere['code'], name=filiere['libelle'], branch=branch).save()
    return HttpResponse('OK', status=200)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def reset_uvs(request: HttpRequest) -> HttpResponse:
    current_year = datetime.now().year
    url = f"https://extranet1.utbm.fr/gpedago/api/guide/uvs/fr/{current_year}"
    uvs = requests.get(url).json()
    codes = [c['code'] for c in uvs]
    to_delete = UV.objects.exclude(code__in=codes)
    if to_delete.exists():
        print("Suppression des UVs")
        to_delete.delete()
    existing = set([i['code'] for i in UV.objects.values('code')])
    for uv in uvs:
        if uv['code'] not in existing:
            try:
                url = f"https://extranet1.utbm.fr/gpedago/api/guide/uv/fr/" \
                      f"{current_year}/{uv['code']}/{uv['codeFormation']}"
                UV.save_from_json(requests.get(url).json())
                print(f'UV {uv["code"]} saved')
            except Exception as e:
                print(e, uv['code'])
    return HttpResponse('OK', status=200)


@login_required
@require_GET
def get_uvs(request: HttpRequest) -> HttpResponse:
    form = UVSearchForm(request.GET)
    if request.GET:
        uvs = form.to_uv_queryset()
    else:
        uvs = [uv.uv for uv in request.user.followed_uvs.all()]
    data = serializers.serialize('python', uvs)
    data = json.dumps([d["fields"] for d in data])
    return HttpResponse(data, content_type='application/json')


@login_required
@require_GET
def download_annal(request: HttpRequest, annal_id: int) -> HttpResponse:
    """
    Renvoie à l'utilisateur le fichier téléchargeable correspondant
    à l'annale dont l'id est passé en paramètre
    """
    annal = Annal.objects.get(id=annal_id)
    image_buffer = open(annal.file.path, "rb").read()
    file_type = mimetypes.guess_type(annal.file.path)[0]
    response = HttpResponse(image_buffer, content_type=file_type)
    file_name = f"{annal.uv.code}_{annal.semester}_{annal.get_exam_type_display()}.{annal.file.name.split('.')[-1]}"
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    return response


@login_required
@require_POST
@permission_required('annals.delete_annal')
def delete_annal(request: HttpRequest, annal_id: int) -> HttpResponse:
    """
    Supprime l'annale dont l'id est passé en paramètre
    """
    try:
        annal = Annal.objects.get(id=annal_id)
    except Annal.DoesNotExist:
        return HttpResponse('Annal not found', status=404)
    annal.file.delete()
    annal.delete()
    return HttpResponse('OK', status=200)


@login_required
@require_POST
@permission_required('annals.approve_annal')
def approve_annal(request: HttpRequest, annal_id: int) -> HttpResponse:
    """
    Approuve l'annale dont l'id est passé en paramètre
    """
    try:
        annal = Annal.objects.get(id=annal_id)
    except Annal.DoesNotExist:
        return HttpResponse('Annal not found', status=404)
    annal.status = Annal.Status.APPROVED
    annal.save()
    return HttpResponse('OK', status=200)


@login_required
@require_POST
def register_review(request: HttpRequest) -> HttpResponse:
    form = ReviewForm(request.POST)
    if form.is_valid():
        uv = form.cleaned_data['uv']
        form.cleaned_data['status'] = Review.Status.PENDING
        _, created = Review.objects.update_or_create(author=request.user, uv=uv, defaults=form.cleaned_data)
        if created:
            return HttpResponse("created", status=200)
        else:
            return HttpResponse("updated", status=200)
    else:
        return HttpResponse("invalid", status=400)


@login_required
@permission_required('pedagogy.validate_review')
@require_POST
def review_validate(request: HttpRequest, review_id: int) -> HttpResponse:
    """
    Valide le commentaire dont l'id est passé en paramètre.
    """
    try:
        review = Review.objects.get(id=review_id)
    except Review.DoesNotExist:
        return HttpResponse(status=404)
    review.status = Review.Status.APPROVED
    review.save()
    return HttpResponse(status=200)


@login_required
@permission_required('pedagogy.')
@require_POST
def review_delete(request: HttpRequest, review_id: int) -> HttpResponse:
    """
    Supprime le commentaire dont l'id est passé en paramètre.
    Les utilisateurs ayant le droit de supprimer un commentaire sont ceux ayant la permission
    'pedagogy.delete_review' plus l'auteur du commentaire.

    :return: HttpResponse:
    status=200 si la suppression a été effectuée ;
    status=403 si l'utilisateur n'a pas les droits (que la ressource existe ou non) ;
    status=404 si l'utilisateur a les droits mais que la ressource n'existe pas
    """
    # L'utilisateur doit pouvoir supprimer le message s'il en a les droits ou s'il en est l'auteur
    # pour vérifier cette condition, on doit le faire à l'intérieur de la fonction, sans décorateur
    # l'ordre des conditions est peut-être un peu compliqué, mais c'est nécessaire
    # pour que si l'utilisateur n'a pas les droits et que le commentaire demandé n'existe pas,
    # on retourne une erreur 403 et pas 404
    review = Review.objects.filter(id=review_id).first()
    if not request.user.has_perm('pedagogy.delete_review'):
        if review is None or review.author != request.user:
            return HttpResponse(status=403, reason="You can't delete this review")
        elif review is not None and review.author == request.user:
            review.delete()
            return HttpResponse(status=200, reason="Review deleted")
    elif review is None:
        return HttpResponse(status=404, reason="Review not found")
    else:
        review.delete()
        return HttpResponse(status=200, reason="Review deleted")
