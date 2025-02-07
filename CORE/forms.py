# Ce fichier accueil toutes les classes formulaires associées aux classes entités
# Un objet formulaire permet d'instancier un objet modèle qui sera valorisé
# par les données issues d'un formulaire de la vue/template.


from django import forms
from django.core.exceptions import ValidationError

from CORE.models import Student, Photo


# Formulaire d'instanciation d'un objet de la classe Student :
# ------------------------------------------------------------

class StudentForm(forms.ModelForm):
    class Meta:
        # Champs à inclure dans le formulaire :
        model = Student
        fields = ('last_name',
                  'first_name',)

        # Labels associés aux champs :
        labels = {'last_name': 'Nom de famille',
                  'first_name': 'Prénom',}

        # Valeurs des variables du formulaire :
        widgets = {
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Saisir le nom de famille',
                'title': "Nom de famille de l'élève",
                'aria-label': 'Champ de saisie du nom de famille',
                'required': True,
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Saisir le prénom',
                'title': "Prénom de l'élève",
                'aria-label': 'Champ de saisie du prénom',
                'required': True,
            }),
        }
    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')

        # Vérification de la présence de l'élève dans la B.D. :
        if Student.objects.filter(first_name=first_name, last_name=last_name).exists():
            raise ValidationError("Un élève portant le même nom et prénom existe déjà !")

        return cleaned_data


# Formulaire d'upload et d'instance des fichiers photos :
# -------------------------------------------------------

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True  # Autoriser la sélection multiple

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if data is None:
            return []
        if not isinstance(data, (list, tuple)):
            data = [data]
        return [super(MultipleFileField, self).clean(file, initial) for file in data]

class PhotoForm(forms.Form):
    images = MultipleFileField(label="Sélectionnez des photos", required=False)

