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


class ReviewForm(forms.Form):
    CHOICES = [(i, i) for i in range(0, 5)]
    uv_id = forms.CharField(widget=forms.HiddenInput, required=True)
    comment = forms.CharField(label='comment', widget=forms.Textarea)
    grades = {
        'Note globale': forms.IntegerField(widget=forms.RadioSelect(choices=CHOICES), label="user-grade-global"),
        'Utilité': forms.IntegerField(widget=forms.RadioSelect(choices=CHOICES), label="user-grade-usefulness"),
        'Enseignement': forms.IntegerField(widget=forms.RadioSelect(choices=CHOICES), label="user-grade-teaching"),
        'Intérêt': forms.IntegerField(widget=forms.RadioSelect(choices=CHOICES), label="user-grade-interest"),
        'Charge de travail': forms.IntegerField(widget=forms.RadioSelect(choices=CHOICES), label="user-grade-work_load"),
    }
