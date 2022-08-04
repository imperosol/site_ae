from django.contrib.auth.models import User
from django.db import models


# Create your models here.


class UserProfile(models.Model):
    """
    Modèle servant à étendre les fonctionnalités de Django Auth.
    Les éléments suivants sont ajoutés à l'utilisateur:
    - photo de profil
    - promotion
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='img/profile_pictures', blank=True)
    promo = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return self.user.username
