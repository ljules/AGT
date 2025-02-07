from idlelib.rpc import response_queue

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404

from CORE.forms import StudentForm
from CORE.models import Student
from CORE.utils.import_students_from_csv import import_students_from_csv

from django.contrib.messages import get_messages

# SAISIE MANUELLE D'UN ELEVE :
def sign_up(request):
    # Méthode POST : Traitement du formulaire de saisi d'un nouvel élève/étudiant
    if request.method == "POST":
        form = StudentForm(request.POST)
        # Filtrage des formulaires valides :
        if form.is_valid():
            # Mise en persistance du nouvel objet étudiant dans la B.D. :
            form.save()
            # Affiche du message de confirmation :
            messages.success(request, f"L'élève {form.cleaned_data['last_name']} {form.cleaned_data['first_name']} a été ajouté avec succès !")

            return redirect('ad_a2p:students_sign_up') # Affichage d'un formulaire vide

    # Méthode GET (par défaut) : Affichage de la vue du formulaire
    else:
        form = StudentForm()

    # Réponse aux requêtes GET - POST :
    return render(request, 'ad_a2p/students_sign_up.html', {'form': form})


# AFFICHAGE DU RESULTAT DE L'IMPORTATION :
def import_result(request):
    """
    Vue pour afficher les résultats de l'importation.
    """
    storage = get_messages(request)
    return render(request, 'ad_a2p/import_result.html', {'messages': storage})


# EDITION DE LA LISTE DES ELEVES DE LA BD :
def editor(request):

    # Récupère le paramètre de tri :
    sort_by = request.GET.get('sort', 'id')  # Tri par défaut : ID
    order = request.GET.get('order', 'asc')  # Ordre par défaut : croissant

    # Détermine l'ordre de tri :
    if order == 'desc':
        sort_by = f'-{sort_by}'  # Ajoute un '-' pour un tri décroissant

    # Récupère les élèves triés :
    students = Student.objects.order_by(sort_by)


    # Configuration de la pagination :
    paginator = Paginator(students, 8)  # 8 élèves par page
    page_number = request.GET.get('page')  # Récupère le numéro de page depuis l'URL
    students = paginator.get_page(page_number)  # Obtiens les élèves pour la page courante

    # Gestion du retour du formulaire :
    if request.method == "POST":
        # Suppression d'un élève :
        if 'delete' in request.POST:
            student_id = request.POST.get('student_id')
            Student.objects.filter(id=student_id).delete()
            return redirect('ad_a2p:students_editor') # Rafraîchit la page après suppression

        # Modification d'un élève :
        else:
            # Récupération de l'élève dans la B.D. à partir de son ID retourné par le formulaire :
            student_id = request.POST.get('student_id')
            student = Student.objects.get(id=student_id)

            # Récupération des données spécifiques de l'élève concerné dans le retour du formulaire :
            student.last_name = request.POST.get(f"last_name_{student_id}")
            student.first_name = request.POST.get(f"first_name_{student_id}")
            student.save()
            return redirect('ad_a2p:students_editor') # Rafraîchit la page après MAJ

    return render(request, 'ad_a2p/students_edition.html', {
                        'students': students,
                        'current_sort': request.GET.get('sort', 'id'),
                        'current_order': order,
    })


# IMPORT DES ELEVES A PARTIR D'UN CSV :
def import_students(request):
    """
    Vue pour importer une liste d'élèves à partir d'un fichier CSV.
    :param request:
    :return:
    """

    if request.method == "POST" and request.FILES.get('csv_file'):
        # Récupération du fichier csv :
        csv_file = request.FILES.get('csv_file')

        # Vérifier si le fichier a l'extension correcte :
        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Le fichier doit être au format CSV.")
            return redirect('ad_a2p:import_result')

        # Appelle la fonction utilitaire d'importation :
        try:
            imported_count, errors = import_students_from_csv(csv_file)
            messages.success(request, f"{imported_count} élève(s) importé(s) avec succès.")
            for error in errors:
                messages.warning(request, error)
        except ValidationError as e:
            messages.error(request, f"Erreur : {e}")
        except Exception as e:
            messages.error(request, f"Une erreur inattendue s'est produite : {e}")

        return redirect('ad_a2p:import_result')

    return render(request, 'ad_a2p/students_sign_up.html')


# AFFICHAGE QR CODE SUR TABLETTE :
def qr_code_tab(request):
    """
    Affiche la page des QR Codes avec la liste déroulante des élèves
    triée par ID en ordre décroissant.
    """

    # Récupération des élèves triés par ID décroissant :
    students = Student.objects.order_by('-id')

    # Sélection de l'élève par défaut (1er de la liste) :
    #selected_student = students.first() if students.exists() else None
    selected_student_id = request.GET.get('student_id', students.first().id if students.exists() else None)
    selected_student = get_object_or_404(Student, id=selected_student_id) if selected_student_id else None

    return render(request, 'ad_a2p/qr_code_on_tab.html', {
        'students': students,
        'selected_student': selected_student,
    })

# AFFICHAGE QR CODE SUR ENI :
def qr_code_ins(request):
    """
    Affiche la page des QR Codes avec la liste déroulante des élèves
    triée par ID en ordre décroissant.
    """

    # Récupération des élèves triés par ID décroissant :
    students = Student.objects.order_by('-id')

    # Sélection de l'élève par défaut (1er de la liste) :
    #selected_student = students.first() if students.exists() else None
    selected_student_id = request.GET.get('student_id', students.first().id if students.exists() else None)
    selected_student = get_object_or_404(Student, id=selected_student_id) if selected_student_id else None

    return render(request, 'ad_a2p/qr_code_on_ins.html', {
        'students': students,
        'selected_student': selected_student,
    })
