from django.contrib import admin

from .models import Branch, Filiere, UV, UVFollow, Review, Annal

# Register your models here.

admin.site.register(Filiere)
admin.site.register(Branch)
admin.site.register(UVFollow)
admin.site.register(Review)


@admin.register(UV)
class UVAdmin(admin.ModelAdmin):
    search_fields = ['code__icontains']


@admin.register(Annal)
class AnnalAdmin(admin.ModelAdmin):
    search_fields = ['uv__code__icontains']
