import cv2  # Import d'OpenCV
import numpy as np
from CORE.models import Photo


def crop_on_face(obj_photo: Photo, scale_factor: float = 1.1, min_neighbors: int = 15, min_size: tuple = (100, 100),
                 ratio_format: tuple[int, int] = (45, 35), margin: float = 0.80) -> None:
    """
    Prend un objet Photo pour appliquer un algorithme de détection de visage
    et met à jour les valeurs des attributs crop_x, crop_y, crop_width et crop_height de l'objet photo.

    Args:
        obj_photo (Photo): Objet Photo à traiter.
        scale_factor (float): A chaque itération l'image est réduite selon le taux (ex: 1.1 pour 10 %).
        min_neighbors (int): Spécifie le nombre de rectangles voisins pour valider une zone comme un visage.
        min_size (tuple): Taille minimale en pixels d'un visage pour être pris en compte.
        ratio_format (tuple[int, int]): Format de l'image avec le rapport hauteur / largeur (ex: 4/3 → (4, 3)).
        margin (float): Pourcentage de pixels à ajouter autour du visage détecté.

    Returns:
        None
    """

    # Chargement de l'image depuis chemin de l'objet photo :
    image_path = obj_photo.image.path
    image = cv2.imread(image_path)

    if image is None:
        print(f"Erreur : Impossible de charger l'image {image_path}")
        return

    # Conversion en niveaux de gris (améliore la détection de visages)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Chargement du classificateur de visages OpenCV
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Détection des visages
    faces = face_cascade.detectMultiScale(gray, scaleFactor=scale_factor, minNeighbors=min_neighbors, minSize=min_size)

    if len(faces) == 0:
        print(f"Aucun visage détecté dans {image_path}")
        return

    # Sélection du premier visage détecté
    x, y, w, h = faces[0]

    # Application d'une marge sur la zone détectée
    margin_w = int(w * margin)
    margin_h = int(h * margin)

    x1 = max(0, x - margin_w)
    y1 = max(0, y - margin_h)
    x2 = min(image.shape[1], x + w + margin_w)
    y2 = min(image.shape[0], y + h + margin_h)

    # Ajustement au ratio demandé
    crop_width = x2 - x1
    crop_height = y2 - y1
    target_height = int(crop_width * (ratio_format[0] / ratio_format[1]))

    if crop_height > target_height:
        # Trop de hauteur, ajuster
        delta = (crop_height - target_height) // 2
        y1 += delta
        y2 -= delta
    else:
        # Trop de largeur, ajuster
        target_width = int(crop_height * (ratio_format[1] / ratio_format[0]))
        delta = (crop_width - target_width) // 2
        x1 += delta
        x2 -= delta

    # Mise à jour des valeurs de l'objet Photo
    obj_photo.crop_x = x1
    obj_photo.crop_y = y1
    obj_photo.crop_width = x2 - x1
    obj_photo.crop_height = y2 - y1
    obj_photo.save(update_fields=['crop_x', 'crop_y', 'crop_width', 'crop_height'])

    print(f"Rognage appliqué : x={x1}, y={y1}, width={obj_photo.crop_width}, height={obj_photo.crop_height}")
