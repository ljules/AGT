import os
import json
import zipfile
from io import BytesIO
from PIL import Image

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib import messages
from django.core.files.storage import default_storage
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from CORE.forms import PhotoForm
from CORE.models import Photo, Student
from CORE.utils.crop_on_face import crop_on_face
from CORE.utils.read_qr_code import read_qr_code
from CORE.utils.correct_orientation import correct_orientation


# HOME HANDLER :
def home_handler(request):
    # Récupérer toutes les instances de Photo
    photos = Photo.objects.all()

    # Récupérer tous les étudiants qui ne sont pas associés à une photo (où fk_id_student est NULL)
    students_without_photo = Student.objects.filter(photo__isnull=True)

    # Transmettre les photos et les étudiants sans photos au template
    context = {
        'photos': photos,
        'students_without_photo': students_without_photo,
    }

    return render(request, 'ad_agt/home_handler.html', context)

# UPLOAD DES PHOTOS SANS FILEPOND :
# def upload_photos(request):
#     if request.method == 'POST':
#         form = PhotoForm(request.POST, request.FILES)
#         if form.is_valid():
#             files = request.FILES.getlist('images')  # Récupérer tous les fichiers
#             for file in files:
#                 # Créer une instance Photo pour chaque fichier
#                 Photo.objects.create(image=file)
#             return redirect('ad_agt:upload_photos')
#         else:
#             # Afficher les erreurs de validation du formulaire
#             print("Form errors:", form.errors)
#     else:
#         form = PhotoForm()
#     return render(request, 'ad_agt/upload_photos.html', {'form': form})

# UPLOAD DES PHOTOS AVEC FILEPOND :
# @csrf_exempt
def upload_photos(request):
    if request.method == 'POST':
        files = request.FILES.getlist('images')  # Récupérer tous les fichiers
        for file in files:
            # Extraire le nom du fichier uploadé
            uploaded_file_name = os.path.basename(file.name)
            #print(f"Nom du fichier avant traitement : {file.name}")  # Débogage

            # Vérifier si une photo avec le même nom de fichier existe déjà
            existing_photo = Photo.objects.filter(file_name=uploaded_file_name).first()

            if existing_photo:
                # Si une photo existe, mettre à jour le fichier
                existing_photo.image.delete(save=False)  # Supprimer l'ancien fichier
                existing_photo.image = file  # Mettre à jour avec le nouveau fichier
                existing_photo.save()  # Sauvegarder les modifications
            else:
                # Si la photo n'existe pas, créer une nouvelle instance
                photo = Photo.objects.create(image=file, file_name=uploaded_file_name)
                #print(f"Nom du fichier après traitement : {photo.image.name}")  # Débogage

        messages.success(request, 'Les photos ont été uploadées avec succès.')
    return render(request, 'ad_agt/upload_photos.html')


# ENREGISTREMENT DU ROGNAGE DES IMAGES :
# @csrf_exempt
def save_crop_coordinates(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        photo_id = data.get('photo_id')
        crop_x = data.get('crop_x')
        crop_y = data.get('crop_y')
        crop_width = data.get('crop_width')
        crop_height = data.get('crop_height')

        try:
            photo = Photo.objects.get(id=photo_id)
            photo.crop_x = crop_x
            photo.crop_y = crop_y
            photo.crop_width = crop_width
            photo.crop_height = crop_height
            photo.save()

            return JsonResponse({"success": True, "message": "Coordonnées sauvegardées."})
        except Photo.DoesNotExist:
            return JsonResponse({"success": False, "message": "Photo introuvable."}, status=404)

    return JsonResponse({"success": False, "message": "Requête invalide."}, status=400)


# ROGNER TOUTES LES PHOTOS AVEC LA FONCTION UTILITAIRE CROP_ON_FACE() :
def crop_photos_page(request):
    """
    Affiche la page avec la barre de progression.
    """
    return render(request, 'crop_photos.html')


# ASSOCIER TOUTES LES PHOTOS A UNE ELEVE AVEC LA FONCTION UTILITAIRE READ_QR_CODE() :
# @csrf_exempt
def read_all_qr_codes(request):
    """
    Vue pour lire les QR Codes des photos et envoyer la progression via WebSocket.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            channel_name = data.get("channel_name")

            if not channel_name:
                return JsonResponse({"error": "Aucun channel WebSocket fourni"}, status=400)

            channel_layer = get_channel_layer()
            if not channel_layer.valid_channel_name(channel_name):
                return JsonResponse({"error": "Nom de canal WebSocket invalide"}, status=400)

            photos = Photo.objects.all()
            total_photos = photos.count()

            if total_photos == 0:
                return JsonResponse({"message": "Aucune photo trouvée."})

            count_success = 0
            count_fail = 0

            for index, photo in enumerate(photos, start=1):
                try:
                    read_qr_code(photo)
                    count_success += 1
                except Exception as e:
                    print(f"Erreur sur {photo.image}: {e}")
                    count_fail += 1

                progress = int((index / total_photos) * 100)

                async_to_sync(channel_layer.send)(
                    channel_name,
                    {
                        "type": "send.progress",
                        "progress": progress,
                        "message": f"Traitement {index}/{total_photos}..."
                    }
                )

            return JsonResponse({
                "message": f"QR Codes traités : {count_success} succès, {count_fail} échecs."
            })
        except json.JSONDecodeError:
            return JsonResponse({"error": "Requête invalide"}, status=400)

    return JsonResponse({"error": "Méthode non autorisée"}, status=405)


# AJOUT D'UNE ASSOCIATION ELEVE-PHOTO :
# @csrf_exempt
def update_student_association(request):
    if request.method == 'POST':
        try:
            # Récupérer les données de la requête AJAX
            data = json.loads(request.body)
            photo_id = data.get('photo_id')
            last_name = data.get('last_name')
            first_name = data.get('first_name')

            # Récupérer la photo et l'élève correspondant
            photo = get_object_or_404(Photo, id=photo_id)
            student = Student.objects.get(last_name=last_name, first_name=first_name)

            # Mettre à jour la photo avec l'élève associé
            photo.fk_id_student = student
            photo.save()

            # Retourner une réponse JSON
            return JsonResponse({"success": True, "message": "Association mise à jour avec succès."})
        except Student.DoesNotExist:
            return JsonResponse({"success": False, "message": "Élève introuvable."}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)
    return JsonResponse({"success": False, "message": "Requête invalide."}, status=400)


# SUPPRESSION D'UNE PHOTO (objet + fichier) :
# @csrf_exempt
def delete_photo(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        photo_id = data.get('photo_id')

        try:
            photo = get_object_or_404(Photo, id=photo_id)

            # Suppression du fichier associé à l'objet :
            if photo.image:
                photo.image.delete(save=False)

            # Suppresion de l'objet photo :
            photo.delete()

            return JsonResponse({"success": True, "message": "Photo supprimée avec succès."})

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)

    return JsonResponse({"success": False, "message": "Requête invalide."}, status=400)


# SUPPRESSION DU LIEN ENTRE LA PHOTO & UN ETUDIANT/ELEVE :
# @csrf_exempt
def remove_student_association(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        photo_id = data.get('photo_id')

        try:
            photo = get_object_or_404(Photo, id=photo_id)
            photo.fk_id_student = None
            photo.save()

            return JsonResponse({"success": True, "message": "L'association de l'élève a été supprimée."})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)

    return JsonResponse({"success": False, "message": "Requête invalide."}, status=400)


# SUPPRESSION DE TOUS LES LIENS ENTRE LES PHOTOS & LEURS ELEVES :
# @csrf_exempt
def remove_all_students_from_photos(request):
    if request.method == "POST":
        try:
            # Met à jour toutes les photos en mettant fk_id_student à NULL
            Photo.objects.update(fk_id_student=None)
            return JsonResponse({"success": True, "message": "Tous les liens photo-élève ont été supprimés."})
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Erreur : {str(e)}"})
    return JsonResponse({"success": False, "message": "Requête invalide."}, status=400)


# SUPPRESSION DE TOUTES LES PHOTOS (objets + fichiers)
@csrf_exempt
def delete_all_photos(request):
    if request.method == 'POST':
        try:
            # Récupérer toutes les photos
            photos = Photo.objects.all()

            # Supprimer les fichiers associés
            for photo in photos:
                if photo.image:
                    photo.image.delete(save=False)  # Supprime le fichier de stockage

            # Supprimer tous les objets Photo
            photos.delete()

            return JsonResponse({"success": True, "message": "Toutes les photos ont été supprimées avec succès."})
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Erreur : {str(e)}"}, status=500)

    return JsonResponse({"success": False, "message": "Requête invalide."}, status=400)



# DOWNLOAD DES PHOTOS :
def download_photos(request):
    return render(request, 'ad_agt/download_photos.html')


def download_processed_photos(request):
    if request.method == "POST":
        order = request.POST.get("order")
        separator = request.POST.get("separator")

        if not order or not separator:
            return HttpResponse("Format de nom de fichier non sélectionné.", status=400)

        # Vérification de l'existence du dossier media/photos
        photos_dir = os.path.join(settings.MEDIA_ROOT, 'photos')
        if not os.path.exists(photos_dir):
            return HttpResponse("Le dossier de stockage des photos est introuvable.", status=500)

        # Création d'une archive ZIP
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for photo in Photo.objects.filter(fk_id_student__isnull=False):
                student = photo.fk_id_student
                if not student:
                    continue

                # Formatage du nom de fichier
                if order == "last_first":
                    file_name = f"{student.last_name}{separator}{student.first_name}.jpg"
                else:
                    file_name = f"{student.first_name}{separator}{student.last_name}.jpg"

                # Obtenir le chemin complet de l'image
                image_path = os.path.join(settings.MEDIA_ROOT, photo.image.name)

                # Vérifier si le fichier existe avant d'essayer de l'ouvrir
                if not os.path.exists(image_path):
                    print(f"Fichier non trouvé : {image_path}")
                    continue

                # Ouvrir l'image et appliquer le recadrage
                with Image.open(image_path) as img:
                    img = correct_orientation(img)  # Redresse l'image si nécessaire

                    # Appliquer le rognage :
                    crop_box = (photo.crop_x, photo.crop_y,
                                photo.crop_x + photo.crop_width,
                                photo.crop_y + photo.crop_height)
                    cropped_img = img.crop(crop_box)

                    # Sauvegarde dans un buffer mémoire
                    img_io = BytesIO()
                    cropped_img.save(img_io, format="JPEG")
                    img_io.seek(0)

                    # Ajout au fichier ZIP
                    zip_file.writestr(file_name, img_io.getvalue())

        # Préparer la réponse avec le fichier ZIP
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="photos_recadrees.zip"'
        return response

    return render(request, 'ad_agt/download_photos.html')
