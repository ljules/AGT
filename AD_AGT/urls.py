from django.urls import path
from . import views

app_name = 'ad_agt'  # Namespace pour les URLs de cette application

urlpatterns = [
    path('home-handler/', views.home_handler, name='home_handler'),
    path('upload-photos/', views.upload_photos, name='upload_photos'),
    path('download-photos/', views.download_photos, name='download_photos'),
    path('download-processed-photos/', views.download_processed_photos, name='download_processed_photos'),
    path('download-success/', views.download_success, name='download_success'),
    path('home-handler/save-crop-coordinates/', views.save_crop_coordinates, name='save_crop_coordinates'),
    path('home-handler/crop-all-photos/', views.crop_all_photos, name='crop_all_photos'),
    path('home-handler/update-student-association/', views.update_student_association, name='update_student_association'),
    path('home-handler/delete-photo/', views.delete_photo, name='delete_photo'),
    path('home-handler/remove-student-association/', views.remove_student_association, name='remove_student_association'),
    #path('home-handler/crop_all/', views.crop_all_faces, name='crop_all'),
    #path('home-handler/get_crop_progress/', views.get_crop_progress, name='get_crop_progress'),
    path("home-handler/read-all-qr-codes/", views.read_all_qr_codes, name="read_all_qr_codes"),
    path('home_handler/remove-all-students/', views.remove_all_students_from_photos, name='remove_all_students'),
    path('home-handler/delete-all-photos/', views.delete_all_photos, name='delete_all_photos'),
]