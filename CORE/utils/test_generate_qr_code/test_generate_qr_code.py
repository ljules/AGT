import os
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AGT.settings')  # Remplace 'AGT' par le nom de ton projet
django.setup()

from CORE.utils.generate_qr_code import generate_qr_code
import os

# Fonction de test
def run_test():
    output_dir = "resultat_test_qr_code"
    dir_path = os.path.join(
        os.path.dirname(__file__),  # Répertoire actuel du script
        output_dir  # Nom du répertoire
    )

    # Liste des clés primaires à tester
    student_ids = [1, 2, 3, -1, 999999]  # Inclut des cas valides et non valides

    # Tester chaque ID étudiant
    for student_id in student_ids:
        print(f"Test pour student_id={student_id}...")
        success = generate_qr_code(student_id, dir_path)

        if success:
            print(f"QR Code généré avec succès pour student_id={student_id} !")
        else:
            print(f"Échec de la génération du QR Code pour student_id={student_id}.")

    print(f"\nLes QR Codes générés (le cas échéant) se trouvent dans : {os.path.abspath(dir_path)}")

if __name__ == "__main__":
    run_test()
