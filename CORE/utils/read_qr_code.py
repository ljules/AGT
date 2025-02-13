import cv2  # Import OpenCV
from CORE.models import Photo, Student

def read_qr_code(obj_photo: Photo) -> None:
    """
    Détecte le premier QR Code présent sur l'image associée à l'objet Photo.
    Si un QR Code est trouvé et correspond à un étudiant existant,
    alors l'attribut fk_id_student est mis à jour avec cet étudiant.

    Args:
        obj_photo (Photo): Objet photo à analyser.

    Returns:
        None
    """

    # Chargement de l'image depuis le chemin de l'objet photo
    image_path = obj_photo.image.path
    image = cv2.imread(image_path)

    # Vérifier si l'image est bien chargée
    if image is None:
        print(f"⚠️ Impossible de charger l'image : {image_path}")
        return

    # Création du détecteur de QR Code
    detector = cv2.QRCodeDetector()

    # Décodage du QR Code
    data, bbox, _ = detector.detectAndDecode(image)

    if data:
        print(f"{obj_photo.image} : ✅ QR Code détecté : {data}")

        # Vérification de l'existence de l'élève correspondant au QR Code
        try:
            student = Student.objects.get(pk=data)
            obj_photo.fk_id_student = student                # Association de l'élève
            obj_photo.save(update_fields=['fk_id_student'])  # Sauvegarde de l'objet mis à jour
            print(f"✅ Élève associé : {student} à la photo {obj_photo.image.name}")
        except Student.DoesNotExist:
            print(f"❌ Aucun élève trouvé avec l'ID {data}. Aucune mise à jour effectuée.")

    else:
        print(f"{obj_photo.image} : ❌ Aucun QR Code détecté.")
