import os
import json
import zipfile
from io import BytesIO
from PIL import Image

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from CORE.forms import PhotoForm
from CORE.models import Photo, Student
from CORE.utils.crop_on_face import crop_on_face
from CORE.utils.read_qr_code import read_qr_code
from CORE.utils.correct_orientation import correct_orientation
from CORE.views import simple_auth_required


# HOME HANDLER :
@simple_auth_required
def home_handler(request):

    # Récupérer & appliquer le statut du verrouillage :
    flip_lock = request.GET.get('flip-lock', None)
    photo_id = request.GET.get('photo-id', None)
    print(f"flip_lock est : {flip_lock} sur la photo id : {photo_id}")
    if flip_lock == 'flip':
        photo = Photo.objects.get(id=photo_id)
        photo.crop_lock = not photo.crop_lock
        photo.save()


    # Récupérer & appliquer les options de filtrage :
    filter_type = request.GET.get('filter', None)
    print(f"Statut du filtre :{filter_type}")
    # Récupérer uniquement les photos non assignées à un étudiant :
    if filter_type == 'unassigned':
        photos = Photo.objects.filter(fk_id_student__isnull=True)

    # Récupérer uniquement les photos non cadrées :
    elif filter_type == 'no-cropped':
        photos = Photo.objects.filter(cropped=False)
    # Récupérer toutes les instances de Photo :
    else:
        photos = Photo.objects.all()

    # Pagination des photos :
    page_number = request.GET.get('page', 1)
    paginator = Paginator(photos, 8)  # Nombre d'éléments par page
    page_obj = paginator.get_page(page_number)

    # Récupérer tous les étudiants qui ne sont pas associés à une photo (où fk_id_student est NULL)
    students_without_photo = Student.objects.filter(photo__isnull=True)

    # Transmettre les photos et les étudiants sans photos au template
    context = {
        'photos': page_obj,
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
@simple_auth_required
def upload_photos(request):
    if request.method == 'POST':
        # 📂 Support FilePond : un seul fichier envoyé sous le champ "file"
        if 'file' in request.FILES:
            files = [request.FILES['file']]
        else:
            files = request.FILES.getlist('images')  # Formulaire classique

        for file in files:
            uploaded_file_name = os.path.basename(file.name)

            # 🔄 Vérifie si une photo avec le même nom existe
            existing_photo = Photo.objects.filter(file_name=uploaded_file_name).first()

            if existing_photo:
                # 🗑️ Supprimer l'ancien fichier et remplacer
                if existing_photo.image:
                    existing_photo.image.delete(save=False)
                existing_photo.image = file
                existing_photo.save()
            else:
                # ➕ Créer une nouvelle entrée
                Photo.objects.create(image=file, file_name=uploaded_file_name)

        # 🔁 Réponse pour appel AJAX (FilePond)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok'})

        # ✅ Sinon, retour classique avec message
        messages.success(request, 'Les photos ont été uploadées avec succès.')

    return render(request, 'ad_agt/upload_photos.html')


# ENREGISTREMENT DU ROGNAGE DES IMAGES :
# @csrf_exempt
@simple_auth_required
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
            photo.cropped = True
            photo.crop_lock = True
            photo.save()

            return JsonResponse({"success": True, "message": "Coordonnées sauvegardées."})
        except Photo.DoesNotExist:
            return JsonResponse({"success": False, "message": "Photo introuvable."}, status=404)

    return JsonResponse({"success": False, "message": "Requête invalide."}, status=400)


# ROGNER TOUTES LES PHOTOS AVEC LA FONCTION UTILITAIRE CROP_ON_FACE() :
@simple_auth_required
def crop_all_photos(request):
    """
    Vue pour recadrer toutes les photos et envoyer la progression en temps réel via WebSockets.
    """
    photos = Photo.objects.all()
    total = len(photos)

    if total == 0:
        return JsonResponse({"success": False, "message": "Aucune photo à recadrer."}, status=400)

    channel_layer = get_channel_layer()
    for index, photo in enumerate(photos, start=1):
        if not photo.crop_lock:
            photo.cropped = crop_on_face(photo) or photo.cropped  # appel de la fonction de rognage et mis à jour de cropped
            photo.save(update_fields=['cropped'])
        progress = int((index / total) * 100)

        # Envoi de la progression au WebSocket via le groupe :
        async_to_sync(channel_layer.group_send)(
            "progress_updates",
            {
                "type": "send_progress",
                "task": "crop", # Identifiant de la tâche
                "progress": progress,
                "message": f"Recadrage {index}/{total}..."
            }
        )

    return JsonResponse({"success": True, "message": "Recadrage terminé."})


# ASSOCIER TOUTES LES PHOTOS A UNE ELEVE AVEC LA FONCTION UTILITAIRE READ_QR_CODE() :
# @csrf_exempt
@simple_auth_required
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

                # Envoi de la progression au WebSocket via le groupe :
                async_to_sync(channel_layer.group_send)(
                    channel_name,
                    {
                        "type": "send.progress",
                        "task": "qr_code", # Identifiant de la tâche
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
#@csrf_exempt
@simple_auth_required
def update_student_association(request):
    if request.method == 'POST':
        try:
            # Récupérer les données de la requête AJAX
            data = json.loads(request.body)
            photo_id = data.get('photo_id')
            student_id = data.get('student_id')
            student_name = data.get('student_name')
            print(f"photo_id: {photo_id} pour associer à : {student_name}")
            # Récupérer la photo et l'élève correspondant
            photo = get_object_or_404(Photo, id=photo_id)
            student = Student.objects.get(id=student_id)

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
@simple_auth_required
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
@simple_auth_required
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
@simple_auth_required
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
# @csrf_exempt
@simple_auth_required
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
@simple_auth_required
def download_photos(request):
    return render(request, 'ad_agt/download_photos.html')


@simple_auth_required
def download_processed_photos(request):
    """
    Vue qui génère une archive ZIP des photos recadrées et informe WebSocket de la progression.
    """
    if request.method == "POST":
        order = request.POST.get("order")
        separator = request.POST.get("separator")

        if not order or not separator:
            print(f"L'ordre entre Nom & Prénom n'a pas été choisi !" if not order else f"L'ordre entre Nom & Prénom est choisi.")
            print(f"Le séparateur n'a pas été choisi !" if not separator else f"Le séparateur est choisi.")
            return JsonResponse({"error": "Format de nom de fichier non sélectionné."}, status=400)

        photos = Photo.objects.filter(fk_id_student__isnull=False)
        total_photos = len(photos)
        print(f"Nombre de photos : {total_photos}")
        if total_photos == 0:
            return JsonResponse({"error": "Aucune photo à traiter."}, status=400)

        zip_buffer = BytesIO()
        channel_layer = get_channel_layer()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for index, photo in enumerate(photos, start=1):
                student = photo.fk_id_student
                if not student:
                    continue

                # Formatage du nom du fichier selon l'ordre choisi
                file_name = f"{student.last_name}{separator}{student.first_name}.jpg" if order == "last_first" else f"{student.first_name}{separator}{student.last_name}.jpg"
                image_path = os.path.join(settings.MEDIA_ROOT, photo.image.name)

                if not os.path.exists(image_path):
                    continue

                with Image.open(image_path) as img:
                    img = correct_orientation(img)  # Corrige l'orientation si nécessaire

                    # Application du rognage
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

                # Envoi de la progression au WebSocket
                progress = int((index / total_photos) * 100)
                async_to_sync(channel_layer.group_send)(
                    "progress_updates",
                    {
                        "type": "send_progress",
                        "task": "download",  # Identifiant de la tâche
                        "progress": progress,
                        "message": f"Téléchargement {index}/{total_photos}..."
                    }
                )

        # Finalisation du ZIP et retour de la réponse
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="photos_recadrees.zip"'

        # Envoi du message de fin via WebSocket
        async_to_sync(channel_layer.group_send)(
            "progress_updates",
            {
                "type": "send_progress",
                "task": "download",
                "progress": 100,
                "message": "🎉 Téléchargement terminé !"
            }
        )

        return response

    # elif request.method == "GET":
    #     # Afficher une page de confirmation après téléchargement
    #     return render(request, 'ad_agt/download_success.html')

    return JsonResponse({"error": "Méthode non autorisée."}, status=405)

@simple_auth_required
def download_success(request):
    """
    Vue pour afficher un message de succès après le téléchargement.
    """
    return render(request, 'ad_agt/download_success.html')
