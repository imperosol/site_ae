from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .forms import UVSearchForm
from .models import UV, Review


@login_required
@require_GET
def uv_search(request: HttpRequest) -> HttpResponse:
    return render(request, 'pedagogy/uvs.html', context={'form': UVSearchForm()})


@login_required
@require_GET
def uv_detail(request: HttpRequest, uv_code: str) -> HttpResponse:
    """
    Renvoie la page html correspondant à l'UV dont le code est passé en paramètre.
    """
    uv = UV.objects.get(code=uv_code)
    # TODO faire le redirect quand l'UE n'existe pas
    grade_types = 'grade_global', 'grade_usefulness', 'grade_interest', 'grade_teaching', 'grade_work_load'
    grades = uv.reviews.values(*grade_types)
    if grades.exists():
        grade_dict = dict()
        for grade_type in grade_types:
            val = grades.aggregate(Avg(grade_type))[f'{grade_type}__avg']
            key = grade_type.removeprefix('grade_')
            if val is not None:
                grade_dict[key] = round(val)
    else:
        grade_dict = {'global': 0, 'usefulness': 0, 'interest': 0, 'teaching': 0, 'work_load': 0}
    reviews = uv.reviews.all()
    if not request.user.has_perm('pedagogy.delete_review'):
        reviews = reviews.filter(status=Review.Status.APPROVED)
    context = {
        'uv': uv,
        'grade': grade_dict,
        'annals': uv.annals.all(),
        'reviews': reviews,
    }
    return render(request, 'pedagogy/uv_detail.html', context=context)


@require_POST
@login_required
def register_review(request: HttpRequest) -> HttpResponse:
    form = UVSearchForm(request.POST)
    return render(request, 'pedagogy/uv_detail.html')
