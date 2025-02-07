from django.urls import path
from . import views

app_name = 'ad_a2p'  # Namespace pour les URLs de cette application

urlpatterns = [
    path('students-sign-up/', views.sign_up, name='students_sign_up'),
    path('student-sign-up/import-students', views.import_students, name='import_students'),
    path('import-result/', views.import_result, name='import_result'),
    path('students-editor/', views.editor, name='students_editor'),
    path('qr-code-tab', views.qr_code_tab, name='qr_code_tab'),
    path('qr-code-ins', views.qr_code_ins, name='qr_code_ins'),
]