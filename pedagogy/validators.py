import re
from django.core.exceptions import ValidationError
from datetime import datetime


def validate_semester(semester: str) -> None:
    """
    Validateur pour un string représentant un semestre.
    Le string doit être de la forme 'XYYYY', où X vaut 'A' ou 'P', en majuscule,
    et YYYY désigne l'année.
    :raise ValidationError: Si le string passé en paramètre n'est pas un semestre valide.
    """
    if re.match(r"^[A,P]\d{4}$", semester) is None:
        raise ValidationError("Le format du semestre doit être AYYYY ou PYYYY")
    year = int(semester[1:])
    actual_date = datetime.now()
    if actual_date.month < 8 and semester[0] == "A":
        year -= 1
    if year > actual_date.year or year < 2000:
        raise ValidationError("L'année est invalide")



