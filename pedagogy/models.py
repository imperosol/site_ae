from django.contrib.auth.models import User
from django.core import validators
from django.db import models
from django.db.models import Avg

from site_ae import settings
from .validators import validate_semester

# valide des chaines de caractères entre 3 et 10 caractères, tout en majuscules et en chiffres
# sans caractère spéciaux et commençant par une lettre
uv_code_validator = validators.RegexValidator(regex=r'^[A-Z][A-Z/d]{2,9}$', message='Invalid UV code')


class Branch(models.Model):
    """
    Représente une branche de l'UTBM (TC, Info, GM, ...)
    La différence est faite entre les branches sous statut ingénieur et les branches sous statut apprenti.
    """
    class FormationType(models.IntegerChoices):
        ING = (1, 'Ingénieur')
        APING = (2, 'Apprenti Ingénieur')

    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    place = models.CharField(max_length=100, choices=settings.UTBM_LOCATIONS, blank=True)
    formation_type = models.PositiveSmallIntegerField(choices=FormationType.choices, default=FormationType.ING)

    def __str__(self):
        name = self.name.removeprefix("Formation d'ingénieur sous statut ")
        return f"{self.code} - {name}"


class Filiere(models.Model):
    """
    Représente une filière de l'UTBM, caractérisée par son code, son nom complet et la branche à
    laquelle elle est rattachée.
    """
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)

    def __str__(self):
        name = self.name.removeprefix("Formation d'ingénieur sous statut ")
        return f"{self.code} - {name}"


class UV(models.Model):
    """
    Représente une UV enseignée à l'UTBM.
    Ce modèle est assez massif comparé aux autres, donc attention lors de son maniement.

    Les champs du modèle sont:
    - code: le code de l'UV, qui doit être unique et ne doit pas contenir de caractères spéciaux ni de minuscules
    - title: le titre de l'UV
    - credits: le nombre de crédits de l'UV
    - credit_type: le type de crédit de l'UV (CS, TM, ST, OM, QC, EC)
    - branch: la branche à laquelle l'UV est rattachée (certaines UV sont rattachées à plusieurs branches)
    - filiere: la filière à laquelle l'UV est rattachée (certaines UV sont rattachées à plusieurs filières)
    - objectives: les objectifs de l'UV, tels que décrits dans le guide officiel des UVs
    - program: le programme de l'UV tel qu'il apparaît dans le guide officiel des UVs
    - skills: les compétences acquises par l'UV, telles que décrites dans le guide des UVs (attention, dans les
    faits, ce champ est relativement rarement présent)
    - spring: un booléen indiquant si l'UV est disponible au printemps
    - false: un booléen inquiquant si l'UV est disponible en automne
    - spring_manager: le responsable de l'UV au printemps (si l'UE n'est pas disponible au printemps, ce champ vaut null)
    - fall_manager: le responsable de l'UV en automne (si l'UE n'est pas disponible en automne, ce champ vaut null)
    - is_open: booléen indiquant si l'UV est encore enseignée. Lorsqu'une UV est supprimée du guide officiel des UVs,
    préférez mettre cette valeur à False plutôt que de retirer l'UV de la base de données.
    - hours_CM: le nombre d'heures de cours magistraux dans le semestre
    - hours_TD: le nombre d'heures de travaux dirigés dans le semestre
    - hours_TP: le nombre d'heures de travaux pratiques dans le semestre
    - hours_THE: le nombre d'heures de travail personnel dans le semestre
    - hours_PRJ: le nombre d'heures de travail passées sur le ou les projets.
    """
    class Language(models.TextChoices):
        FRENCH = 'Français'
        ENGLISH = 'Anglais'

    class CreditType(models.TextChoices):
        FREE = 'free'
        CS = 'CS'
        TM = 'TM'
        OM = 'OM'
        QC = 'QC'
        EC = 'EC'
        RN = 'RN'
        ST = 'ST'
        EXT = 'EXT'

    code = models.CharField(max_length=10, unique=True, validators=[uv_code_validator])
    title = models.CharField(verbose_name="Nom de l'UV", max_length=100)
    objectives = models.TextField(verbose_name="Objectifs de l'UV")
    program = models.TextField(verbose_name="Programme de l'UV")
    skills = models.TextField(verbose_name="Compétences acquises")
    key_concepts = models.TextField(verbose_name="Concepts clés")
    credits = models.PositiveIntegerField(verbose_name="Crédits")
    credit_type = models.CharField(verbose_name="Type de crédit", choices=CreditType.choices, max_length=4)
    spring_manager = models.CharField(verbose_name="responsable de l'UV", max_length=50, blank=True)
    fall_manager = models.CharField(verbose_name="responsable de l'UV", max_length=50, blank=True)
    spring = models.BooleanField(verbose_name="Printemps")
    fall = models.BooleanField(verbose_name="Automne")
    is_open = models.BooleanField(verbose_name="Ouverte", default=True)
    language = models.CharField(verbose_name="Langue", choices=Language.choices, max_length=20)
    filiere = models.ManyToManyField(Filiere, blank=True)
    branch = models.ManyToManyField(Branch, blank=True)

    # Les heures de travail requises par l'UV
    hours_CM = models.PositiveIntegerField(default=0)  # cours magistraux
    hours_TD = models.PositiveIntegerField(default=0)  # travaux dirigés
    hours_TP = models.PositiveIntegerField(default=0)  # travaux pratiques
    hours_THE = models.PositiveIntegerField(default=0)  # travail personnel
    hours_PRJ = models.PositiveIntegerField(default=0)  # travail sur projets

    @classmethod
    def __add_categories(cls, uv, json):
        sem = "automne" if uv.fall else "printemps"
        spe = [p["specialisations"] for p in json[sem]["profils"]]
        spe = [p for s in spe for p in s]
        fil_id = [i["libelleCourt"] for i in spe]
        uv.save()
        if len(fil_id) > 0:
            fil_id = [fil.id for fil in Filiere.objects.filter(code__in=fil_id)]
            uv.filiere.add(*fil_id)
        uv.branch.add(Branch.objects.get(code=json["codeFormation"]))
        uv.save()

    @classmethod
    def save_from_json(cls, json: dict):
        """
        Sauvegarde toutes les UVs contenues dans le dictionnaire fourni en paramètre.
        C'est assez instable, donc évitez d'utiliser. Genre vraiment.
        """
        if UV.objects.filter(code=json['code']).exists():
            cls.__add_categories(UV.objects.get(code=json['code']), json)
            return
        uv = cls(
            code=json['code'],
            title=json['libelle'],
            objectives=json['objectifs'],
            program=json['programme'],
            skills=json['acquisitionCompetences'],
            language=UV.Language.FRENCH if json['codeLangue'] == "fr" else UV.Language.ENGLISH,
            credits=int(json['creditsEcts']),
            spring=json["printemps"] is not None and json["printemps"]["ouvert"] is True,
            fall=json["automne"] is not None and json["automne"]["ouvert"] is True,
        )
        if uv.spring:
            uv.spring_manager = json['printemps']['responsable']
        if uv.fall:
            uv.fall_manager = json["automne"]["responsable"]
        sem = "automne" if uv.fall else "printemps"
        category = json[sem]["profils"][0]["categorie"].split()
        if len(category) > 0:
            uv.credit_type = (category[0][0] + category[-1][0]).upper()
        else:
            uv.credit_type = cls.CreditType.ST
        hours = {act["libelleCourt"]: act["nbh"] // 60 for act in json["activites"]}
        uv.hours_CM = hours.get("CM", 0)
        uv.hours_TD = hours.get("TD", 0)
        uv.hours_TP = hours.get("TP", 0)
        uv.hours_THE = hours.get("THE", 0)
        uv.hours_PRJ = hours.get("PRJ", 0)
        try:
            cls.__add_categories(uv, json)
        except Exception as e:
            pass
        uv.save()

    def get_grades_means(self) -> dict[str, dict[str, str | int]]:
        """
        Retourne un dictionnaire contenant les moyennes des notes de chaque catégorie pour l'UV.
        Les notes sont arrondies à l'entier le plus proche.
        Chaque élément du dictionnaire est lui-même un dictionnaire contenant
        un couple clef-valeur avec les moyennes des notes de chaque catégorie
        et un autre avec les textes à afficher sur le template.

        Les moyennes sont obtenues en faisant la moyenne des notes de tous les avis liés à l'UV.
        Seuls les commentaires approuvés par la modération sont pris en compte.

        Pour chaque type de note dont la moyenne n'existe pas, la valeur est None.

        Le dictionnaire retourné est de la forme: ::

            {
                'global': {
                    'label': 'note globale',
                    'value': <int ∈ [0;4]> | None
                }, 'usefulness': {
                    'label': 'utilité dans le parcours',
                    'value': <int ∈ [0;4]> | None
                }, 'interest': {
                    'label': 'intérêt personnel',
                    'value': <int ∈ [0;4]> | None
                }, 'teaching': {
                    'label': 'enseignement',
                    'value': <int ∈ [0;4]> | None
                }, 'work_load': {
                    'label': 'charge de travail',
                    'value': <int ∈ [0;4]> | None
                }
            }

        """
        grade_types = 'grade_global', 'grade_usefulness', 'grade_interest', 'grade_teaching', 'grade_work_load'
        labels = 'note globale', 'utilité dans le parcours', 'intérêt personnel', 'enseignement', 'charge de travail'
        grades = self.reviews.filter(status=Review.Status.APPROVED).values(*grade_types)
        grade_dict = dict()
        for grade_type, label in zip(grade_types, labels):
            val = grades.aggregate(Avg(grade_type))[f'{grade_type}__avg']
            key = grade_type.removeprefix('grade_')
            if val is not None:  # arrondir une variable None causerait une erreur
                val = round(val)
            grade_dict[key] = {"label": label, "value": val}
        return grade_dict

    def __str__(self):
        res = f"{self.code} - {self.title} - {self.credits}{self.credit_type}"
        if self.credit_type in [UV.CreditType.CS, UV.CreditType.TM]:
            res += f" - {', '.join(self.branch.values_list('code', flat=True))}"
        return res


class Review(models.Model):
    """
    Représente un commentaire d'un étudiant sur une UV.
    Un objet Review est créé chaque fois qu'un étudiant poste un commentaire sur la page de l'UV correspondante.

    Un objet du modèle Review contient les champs suivants:
    - author: l'étudiant qui a posté le commentaire
    - uv: l'UV décrite par le commentaire
    - comment: le texte du commentaire
    - status: le statut du commentaire (1 = en attente, 2 = validé). Les utilisateurs non administrateurs
    ne devraient pas avoir le droit de voir les commentaires en attente.
    - created_at: la date à laquelle le commentaire a été posté
    - updated_at: la date à laquelle le commentaire a été mis à jour pour la dernière fois
    - grade_global: la note globale donnée à l'UV, dans l'intervalle [0;4]
    - grade_usefulness: la note d'utilité donnée à l'UV, dans l'intervalle [0;4]. Décrit à quel point l'auteur
    a trouvé la matière pertinente pour son parcours.
    - grade_interest: la note d'intérêt donnée à l'UV, dans l'intervalle [0;4]. Décrit l'intérêt personnel de l'auteur
    dans la matière.
    - grade_teaching: la note des enseignants donnée à l'UV, dans l'intervalle [0;4]. Décrit l'avis de l'auteur
    sur les enseignants de l'UV (compétence, pédagogie, etc.)
    - grade_work_load: la note globale donnée à l'UV, dans l'intervalle [0;4]. Décrit la charge de travail de
    la matière.
    """
    class Status(models.IntegerChoices):
        PENDING = (1, 'pending')
        APPROVED = (2, 'approved')

    GRADE_CHOICES = ((i, str(i)) for i in range(5))

    uv = models.ForeignKey(UV, on_delete=models.CASCADE, related_name="reviews")
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.IntegerField(choices=Status.choices, default=Status.PENDING)
    comment = models.TextField(blank=True)
    created_ad = models.DateTimeField(auto_now_add=True)
    updated_ad = models.DateTimeField(auto_now=True)
    grade_global = models.PositiveSmallIntegerField(
        verbose_name="Note globale", validators=[validators.MaxValueValidator(4)], blank=True, null=True
    )
    grade_usefulness = models.PositiveSmallIntegerField(
        verbose_name="Utilité dans le parcours", validators=[validators.MaxValueValidator(4)], blank=True, null=True
    )
    grade_interest = models.PositiveSmallIntegerField(
        verbose_name="Intérêt personnel", validators=[validators.MaxValueValidator(4)], blank=True, null=True
    )
    grade_teaching = models.PositiveSmallIntegerField(
        verbose_name="Enseignement", validators=[validators.MaxValueValidator(4)], blank=True, null=True
    )
    grade_work_load = models.PositiveSmallIntegerField(
        verbose_name="Charge de travail", validators=[validators.MaxValueValidator(4)], blank=True, null=True
    )

    class Meta:
        ordering = ["created_ad"]
        unique_together = ("uv", "author")
        permissions = (
            ("approve_review", "Can approve review"),
        )

    def __str__(self):
        return f"{self.author.username} - {self.uv.code}"

    @property
    def is_approved(self) -> bool:
        """
        Retourne True si le commentaire est validé, False sinon.
        """
        return self.status == self.Status.APPROVED

    @property
    def grade_dict(self) -> dict[str, dict[str, str | int]]:
        """
        Retourne un dictionnaire contenant les notes de l'étudiant sur les différents critères.
        Le format utilisé est directement utilisable par le template grade_stars.html
        """
        return {
            'grade_global': {'label': 'Note globale', 'value': self.grade_global},
            'grade_usefulness': {'label': 'Utilité dans le parcours', 'value': self.grade_usefulness},
            'grade_interest': {'label': 'Intérêt personnel', 'value': self.grade_interest},
            'grade_teaching': {'label': 'Enseignement', 'value': self.grade_teaching},
            'grade_work_load': {'label': 'Charge de travail', 'value': self.grade_work_load},
        }


class UVFollow(models.Model):
    """
    Modèle liant un étudiant à une UV.
    Modèle à utiliser pour représenter les UVs que l'étudiant lors du semestre en cours.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="followed_uvs")
    uv = models.ForeignKey(UV, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'uv')


def get_folder(instance, filename):
    return f"files/annals/{instance.uv.code}/{instance.semester}/{filename}"


class Annal(models.Model):
    """
    Représente une annale d'une UV, avec les fichiers associés (et pas autre chose, espèce d'obsédé sexuel).
    Comme pour Review, un objet Annal peut-être soit en attente, soit approuvé.

    Un objet du modèle Annal contient les champs suivants:
    - publisher: l'utilisateur qui a publié l'annale
    - uv: l'UV à laquelle l'annale est rattachée
    - semester: le semestre durant lequel le sujet est tombé
    - file: le sujet de l'annale
    - status: le statut de l'annale (1 = en attente, 2 = approuvé)
    - exam_type: le type d'examen (Partiel 1, Partiel 2, médian, final...)
    """
    class Status(models.IntegerChoices):
        PENDING = (1, 'pending')
        APPROVED = (2, 'approved')

    class ExamType(models.IntegerChoices):
        PARTIEL = (1, 'partiel')
        PARTIEL_1 = (2, 'partiel 1')
        PARTIEL_2 = (3, 'partiel 2')
        MEDIAN = (4, 'médian')
        FINAL = (5, 'final')
        DM = (6, 'devoir maison')

    publisher = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="annals", null=True)
    uv = models.ForeignKey(UV, on_delete=models.CASCADE, related_name="annals")
    status = models.IntegerField(choices=Status.choices, default=Status.PENDING)
    exam_type = models.IntegerField(choices=ExamType.choices, default=ExamType.PARTIEL)
    semester = models.CharField(max_length=5, validators=[validate_semester])
    file = models.FileField(upload_to=get_folder, blank=True, null=True)

    class Meta:
        ordering = ["semester", "uv", "exam_type"]
        permissions = (
            ("approve_annal", "Can approve annal"),
        )

    @property
    def is_approved(self) -> bool:
        """
        Retourne True si l'annale est approuvée, False sinon.
        """
        return self.status == self.Status.APPROVED

