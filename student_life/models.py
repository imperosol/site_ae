from django.contrib.auth.models import User
from django.db import models


# Create your models here.


class Club(models.Model):
    name = models.CharField(max_length=64)
    short_description = models.CharField(max_length=256)
    description = models.TextField()
    logo = models.ImageField(upload_to='static/img/club_logos/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.name


CLUB_ROLES = (
    ('président', 'Président'), ('secrétaire', 'Secrétaire'), ('trésorier', 'Trésorier'),
    ('membre', 'Membre'), ('respo comm', 'Responsable communication'), ('vice-président', 'Vice-président'),
    ('respo partenariats', 'Responsable partenariats')
)


class ClubMember(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    club = models.ForeignKey(Club, related_name='members', on_delete=models.CASCADE)
    member_since = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    is_in_bureau = models.BooleanField(default=False)
    is_president = models.BooleanField(default=False)
    poste = models.CharField(max_length=64, choices=CLUB_ROLES, default='membre')

    def __str__(self):
        return self.user.username
