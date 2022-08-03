from django.contrib import admin

from .models import Branch, Filiere, UV, UVFollow, Review, Annal

# Register your models here.

admin.site.register(Filiere)
admin.site.register(Branch)
admin.site.register(UV)
admin.site.register(UVFollow)
admin.site.register(Review)
admin.site.register(Annal)
