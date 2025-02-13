from PIL import Image, ExifTags

def correct_orientation(image):
    """
    Corrige l'orientation de l'image en fonction des données EXIF.
    """
    try:
        exif = image._getexif()
        if exif:
            for tag, value in exif.items():
                if tag in ExifTags.TAGS and ExifTags.TAGS[tag] == "Orientation":
                    if value == 3:
                        image = image.rotate(180, expand=True)
                    elif value == 6:
                        image = image.rotate(270, expand=True)
                    elif value == 8:
                        image = image.rotate(90, expand=True)
                    break
    except (AttributeError, KeyError, IndexError):
        pass  # Aucun EXIF ou erreur lors de la lecture

    return image
