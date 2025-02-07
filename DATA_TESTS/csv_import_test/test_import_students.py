import os
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AGT.settings')  # Remplace 'AGT' par le nom de ton projet
django.setup()

from CORE.models import Student
from CORE.utils.import_students_from_csv import import_students_from_csv


def run_test():
    """
    Teste l'importation d'élèves à partir d'un fichier CSV.
    """
    # Chemin absolu du fichier CSV
    file_path = os.path.join(
        os.path.dirname(__file__),  # Répertoire actuel du script
        'liste_étudiants_test_import.csv'  # Nom du fichier
    )

    # Vérifie que le fichier existe
    if not os.path.exists(file_path):
        print(f"Fichier introuvable : {file_path}")
        return

    # Ouvre le fichier en mode binaire (comme le ferait Django avec request.FILES)
    with open(file_path, 'rb') as csv_file:
        # Appelle la fonction utilitaire
        imported_count, errors = import_students_from_csv(csv_file)

        # Affiche les résultats
        print(f"{imported_count} élèves importés avec succès.")
        if errors:
            print("Erreurs rencontrées :")
            for error in errors:
                print(f" - {error}")


def cleanup_test_data():
    """
    Supprime toutes les données de test dans la table Student.
    """
    Student.objects.all().delete()
    print("Données de test supprimées.")


if __name__ == "__main__":
    # Nettoyage avant le test
    cleanup_test_data()

    # Exécution du test
    try:
        run_test()
    finally:
        # Nettoyage après le test
        cleanup_test_data()
