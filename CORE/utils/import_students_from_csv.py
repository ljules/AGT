import csv
from django.core.exceptions import ValidationError
from CORE.models import Student


def import_students_from_csv(file):
    """
    Importe une liste d'élèves à partir d'un fichier CSV et les enregistre dans la base de données.

    Le fichier CSV doit contenir les colonnes suivantes (noms sensibles à la casse) :
        - first_name : Prénom de l'élève (obligatoire).
        - last_name : Nom de l'élève (obligatoire).

    Cette fonction effectue les actions suivantes :
        - Lit le contenu du fichier CSV.
        - Valide la présence des champs obligatoires.
        - Vérifie si l'élève existe déjà dans la base de données.
        - Ajoute les nouveaux élèves dans la base de données.

    Paramètres :
    ------------
    file : UploadedFile (de Django ou tout objet de fichier compatible)
        Le fichier CSV contenant les données des élèves. Il doit être encodé en UTF-8.

    Retourne :
    ---------
    tuple : (int, list)
        - int : Le nombre d'élèves importés avec succès.
        - list : Une liste de messages d'erreurs sous forme de chaînes de caractères.
          Chaque message décrit une erreur rencontrée pendant l'importation.

    Exceptions :
    ------------
    ValidationError :
        - Si le fichier ne peut pas être lu ou est mal formaté.
        - Si les champs obligatoires (first_name, last_name) sont absents.

    Exemples d'utilisation :
    ------------------------
    >>> with open('students.csv', 'rb') as csv_file:
    >>>     imported_count, errors = import_students_from_csv(csv_file)
    >>> print(f"{imported_count} élèves importés avec succès.")
    >>> if errors:
    >>>     for error in errors:
    >>>         print(f"Erreur : {error}")
    """



    # Initialisation des résultats
    imported_count = 0
    errors = []

    try:
        # Décodage du fichier (utf-8)
        decoded_file = file.read().decode('utf-8').splitlines()
        csv_reader = csv.DictReader(decoded_file)
    except Exception as e:
        raise ValidationError(f"Erreur lors de la lecture du fichier CSV : {e}")

    # Traitement des lignes du fichier CSV
    for row in csv_reader:
        try:
            # Extraction des champs obligatoires
            first_name = row.get('first_name')
            last_name = row.get('last_name')

            if not first_name or not last_name:
                raise ValidationError(
                    "Les champs 'first_name' et 'last_name' sont obligatoires."
                )

            # Vérification si l'élève existe déjà
            if not Student.objects.filter(first_name=first_name, last_name=last_name).exists():
                # Création de l'élève
                Student.objects.create(
                    first_name=first_name,
                    last_name=last_name
                )
                imported_count += 1
            else:
                errors.append(
                    f"L'élève '{first_name} {last_name}' existe déjà."
                )
        except Exception as e:
            errors.append(f"Erreur sur la ligne {row}: {e}")

    return imported_count, errors
