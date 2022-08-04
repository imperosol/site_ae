from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.http import HttpResponse, HttpRequest
from django.views.decorators.http import require_POST, require_GET
from datetime import datetime
import requests
import mimetypes

from .models import Branch, Filiere, UV, Annal


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
def download_annal(request, annal_id):
    annal = Annal.objects.get(id=annal_id)
    image_buffer = open(annal.file.path, "rb").read()
    file_type = mimetypes.guess_type(annal.file.path)[0]
    print(file_type)
    response = HttpResponse(image_buffer, content_type=file_type)
    file_name = f"{annal.uv.code}_{annal.semester}_{annal.get_exam_type_display()}.{annal.file.name.split('.')[-1]}"
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    return response

