from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from .forms import UVSearchForm, ReviewForm
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
    grades = uv.get_grades_means()
    reviews = uv.reviews.order_by('created_ad')
    reviews = Paginator(reviews, 10).page(1)
    if not request.user.has_perm('pedagogy.delete_review'):
        reviews = reviews.filter(status=Review.Status.APPROVED)
    form = ReviewForm(initial={'uv_id': uv.id})
    context = {
        'form': form,
        'uv': uv,
        'grades': grades,
        'annals': uv.annals.all(),
        'reviews': reviews,
    }
    return render(request, 'pedagogy/uv_detail.html', context=context)


@login_required
@require_POST
def register_review(request: HttpRequest) -> HttpResponse:
    print(dict(request.POST))
    form = ReviewForm(request.POST)
    ue = dict(request.POST).get('uv-code', ['AP4A'])[0]
    return redirect(reverse('pedagogy:uv_detail', kwargs={'uv_code': ue}))
