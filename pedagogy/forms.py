from django.db.models import QuerySet

from utils import get_last_semesters

from django import forms

from .models import Branch, Review, Annal, UV


class UVSearchForm(forms.Form):
    categories = forms.MultipleChoiceField(
        choices=[('CS', 'CS'), ('TM', 'TM'), ('ST', 'ST'), ('OM', 'OM'), ('QC', 'QC'), ('EC', 'EC')],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='Catégories',
        required=False,
    )
    branches_ing = forms.MultipleChoiceField(
        choices=Branch.objects.filter(formation_type=Branch.FormationType.ING).values_list('id', 'code'),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='Branches (statut ingénieur)',
        required=False,
    )
    branches_app = forms.MultipleChoiceField(
        choices=Branch.objects.filter(formation_type=Branch.FormationType.APING).values_list('id', 'code'),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='Branches (statut apprenti ingénieur)',
        required=False,
    )
    name_search = forms.CharField(max_length=20, label='Nom de l\'UV', widget=forms.TextInput(), required=False)

    def to_uv_queryset(self) -> QuerySet[UV]:
        if self.is_valid():
            uvs = UV.objects.filter(code__icontains=self.cleaned_data['name_search'])
            for key in "branches_ing", "branches_app":
                if len(self.cleaned_data[key]) > 0:
                    uvs = uvs.filter(branch__in=self.cleaned_data[key])
            if len(self.cleaned_data["categories"]) > 0:
                uvs = uvs.filter(credit_type__in=self.cleaned_data["categories"])
            return uvs
        else:
            return UV.objects.none()


class AnnaleForm(forms.ModelForm):
    class Meta:
        SEMESTER_CHOICES = [(s, s) for s in get_last_semesters(nb_semesters=6)]
        model = Annal
        fields = ['exam_type', 'file', 'semester']
        widgets = {
            'exam_type': forms.Select(choices=Annal.ExamType),
            'file': forms.FileInput(),
            'semester': forms.Select(choices=SEMESTER_CHOICES),
        }
        labels = {
            'exam_type': 'Type d\'examen',
            'file': 'Fichier',
            'semester': 'Semestre',
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = [
            'uv', 'comment', 'grade_global', 'grade_usefulness',
            'grade_teaching', 'grade_interest', 'grade_work_load'
        ]
        widgets = {
            'uv': forms.HiddenInput,
            'comment': forms.Textarea(),
            'grade_global': forms.RadioSelect(choices=Review.GRADE_CHOICES),
            'grade_usefulness': forms.RadioSelect(choices=Review.GRADE_CHOICES),
            'grade_teaching': forms.RadioSelect(choices=Review.GRADE_CHOICES),
            'grade_interest': forms.RadioSelect(choices=Review.GRADE_CHOICES),
            'grade_work_load': forms.RadioSelect(choices=Review.GRADE_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['grade_global'].label = 'Note globale'
        self.fields['grade_usefulness'].label = 'Utilité dans le parcours'
        self.fields['grade_teaching'].label = 'Enseignement'
        self.fields['grade_interest'].label = 'Intérêt personnel'
        self.fields['grade_work_load'].label = 'Charge de travail'
