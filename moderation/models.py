from django.db import models
from django.contrib.auth.models import User


class ModerationMessage(models.Model):
    class MessageOrigin(models.IntegerChoices):
        SYSTEM = (0, 'Système')
        USER = (1, 'Utilisateur')

    class Status(models.IntegerChoices):
        PENDING = (0, 'En attente')
        APPROVED = (1, 'Approuvé')
        REJECTED = (2, 'Rejeté')

    class Level(models.IntegerChoices):
        INFO = (0, 'Information')
        WARNING = (1, 'Avertissement')
        ERROR = (2, 'Erreur')

    origin = models.PositiveSmallIntegerField(choices=MessageOrigin.choices)
    status = models.PositiveSmallIntegerField(choices=Status.choices)
    message = models.TextField()
    message_closer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    level = models.PositiveSmallIntegerField(choices=Level.choices)
