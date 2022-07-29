import json

from django.core.paginator import Page

from .models import ClubMember


class ClubEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Page):
            return [{
                'id': page.pk,
                'name': str(page.name),
                'description': str(page.description),
                'short_description': page.short_description,
                'logo': str(page.logo),
                'created_at': str(page.created_at.isoformat()),
                'is_active': page.is_active,
                'president': page.president,
            } for page in obj]
        return json.JSONEncoder.default(self, obj)


class ClubMemberEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ClubMember):
            return {
                'id': obj.pk,
                'user_id': obj.user.pk,
                'name': obj.user.username,
                'club': obj.club.name,
                'member_since': str(obj.member_since.isoformat()),
                'is_in_bureau': obj.is_in_bureau,
                'is_president': obj.is_president,
                'poste': obj.poste,
            }
        return json.JSONEncoder.default(self, obj)
