import os
import json
from django.contrib import messages
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from CORE.forms import PhotoForm
from CORE.models import Photo, Student


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
@csrf_exempt
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
@csrf_exempt
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


# AJOUT D'UNE ASSOCIATION ELEVE-PHOTO :
@csrf_exempt
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


# DOWNLOAD DES PHOTOS :
def download_photos(request):
    return render(request, 'ad_agt/download_photos.html')