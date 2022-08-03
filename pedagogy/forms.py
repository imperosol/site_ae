from django import forms
from .models import Branch


class UVSearchForm(forms.Form):
    categories = forms.MultipleChoiceField(
        choices=[('CS', 'CS'), ('TM', 'TM'), ('ST', 'ST'), ('OM', 'OM'), ('QC', 'QC'), ('EC', 'EC')],
        widget=forms.CheckboxSelectMultiple
    )
    branches = forms.MultipleChoiceField(
        choices=[(b.id, b.code) for b in Branch.objects.all()],
        widget=forms.CheckboxSelectMultiple
    )
