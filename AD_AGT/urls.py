from django.urls import path
from . import views

app_name = 'ad_agt'  # Namespace pour les URLs de cette application

urlpatterns = [
    path('home-handler/', views.home_handler, name='home_handler'),
    path('upload-photos/', views.upload_photos, name='upload_photos'),
    path('download-photos/', views.download_photos, name='download_photos'),
    path('home-handler/save-crop-coordinates/', views.save_crop_coordinates, name='save_crop_coordinates'),
    path('home-handler/update-student-association/', views.update_student_association, name='update_student_association'),
]