import os
import segno

def generate_qr_code(student_id, output_dir):
    """
    Génère un QR Code à partir de la clé primaire d'un élève et l'enregistre dans un fichier.

    :param student_id: int
         La clé primaire de l'élève.
    :param output_dir: str
        Le répertoire où le QR Code doit être enregistré.
    :return: bool
        True si le QR Code a été généré et enregistré avec succès, False sinon.
    """

    try:
        # Vérifie que le répertoire de sortie existe, sinon le crée :
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Nom du fichier de sortie (ex : student_1.png) :
        file_path = os.path.join(output_dir, f"qr_student_id_{student_id}.png")

        # Génération du QR Code avec segno :
        qr = segno.make(student_id, encoding='utf-8', error='H')
        qr.save(file_path, scale=40, border=1)  # Génère un fichier PNG avec un scale de 10

        print(f"QR Code pour l'élève ID : {student_id} généré : {file_path}")
        return True

    except Exception as e:
        print(f"Erreur lors de la génération du QR Code pour l'élève ID : {student_id} : {e}")
        return False