from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_GET, require_http_methods

from .forms import UVSearchForm, ReviewForm, AnnaleForm
from .models import UV, Review, Annal


@login_required
@require_GET
def uv_search(request: HttpRequest) -> HttpResponse:
    form = UVSearchForm(request.GET)
    if request.GET:
        uvs = form.to_uv_queryset()
    else:
        uvs = [uv.uv for uv in request.user.followed_uvs.all()]
    context = {'form': form, 'uvs': uvs}
    return render(request, 'pedagogy/uvs.html', context=context)


@login_required
@require_GET
def uv_detail(request: HttpRequest, uv_code: str) -> HttpResponse:
    """
    Renvoie la page html correspondant à l':model:`pedagogy.UV` dont le code est passé en paramètre.

    **Context**

    ``form``
        Une instance de :model:`pedagogy.ReviewForm`
    ``uv``
        Une instance de :model:`pedagogy.UV` correspondant à l'UV dont le code est passé en paramètre dans l'URL
    ``grades``
        Un dictionnaire contenant les notes moyennes attribuées par les étudiants à l'UV, dans le format
        retourné par la méthode `get_grade_means()` de :form:`pedagogy.ReviewForm`
    ``reviews``
        Un ensemble paginé des 10 objets du modèle :model:`pedagogy.Review` dont la création est la plus récente
    ``user_review``
        L'instance du modèle :model:`pedagogy.Review` correspondant au commentaire de l'utilisateur de la session
        en cours. Vaut None si l'utilisateur n'a pas créé de commentaire sur cette UV.
    """
    try:
        uv = UV.objects.get(code=uv_code)
    except UV.DoesNotExist:
        return render(request, 'http_404.html')
    grades = uv.get_grades_means()
    reviews = uv.reviews.order_by('-created_ad')
    reviews = Paginator(reviews, 10).page(1)
    if not request.user.has_perm('pedagogy.delete_review'):
        reviews = reviews.filter(status=Review.Status.APPROVED)
    context = {
        'form': ReviewForm(initial={'uv': uv.id}),
        'uv': uv,
        'grades': grades,
        'reviews': reviews,
        'user_review': uv.reviews.filter(author=request.user).first(),
    }
    return render(request, 'pedagogy/uv_detail/uv_detail.html', context=context)


@login_required
@require_GET
def review_html_fragment(request: HttpRequest, uv_id: int) -> HttpResponse:
    """
    Renvoie juste le bout de code HTML correspondant à un commentaire d'UE.
    Le commentaire dont le rendu est fait est celui posté par l'utilisateur effectuant
    la requête sur l'UE dont l'id est passé en paramètre.

    Si aucun commentaire n'est trouvé, renvoie une erreur 404.
    """
    try:
        review = Review.objects.get(author=request.user, uv_id=uv_id)
    except Review.DoesNotExist:
        return HttpResponse(status=404)
    context = {'review': review}
    return render(request, 'pedagogy/uv_detail/review_item.html', context=context)


@login_required
@require_GET
def uv_grades_fragment(request: HttpRequest, uv_id: int) -> HttpResponse:
    """
    Renvoie juste le bout de code HTML correspondant à la moyenne des notes de l'UE.
    """
    try:
        uv = UV.objects.get(id=uv_id)
    except UV.DoesNotExist:
        return HttpResponse(status=404)
    grades = uv.get_grades_means()
    context = {'grades': grades}
    return render(request, 'pedagogy/uv_detail/global_grades_panel.html', context=context)


@login_required
@require_http_methods(["GET", "POST"])
def annale_add(request: HttpRequest, uv_id: int) -> HttpResponse:
    try:
        uv = UV.objects.get(id=uv_id)
    except UV.DoesNotExist:
        return render(request, 'http_404.html')
    if request.method == 'POST':
        form = AnnaleForm(request.POST, request.FILES)
        if form.is_valid():
            Annal(**form.cleaned_data, publisher=request.user, uv=uv).save()
            return redirect('pedagogy:uv_detail', uv_code=uv.code)
        else:
            return redirect('pedagogy:annale_add', uv_id=uv_id)
    else:
        context = {
            'uv': uv,
            'form': AnnaleForm(initial={'uv': uv_id}),
        }
        return render(request, 'pedagogy/annale_add_form.html', context)
