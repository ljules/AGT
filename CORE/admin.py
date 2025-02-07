from django.contrib import admin
from .models import Student

class StudentAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'first_name',
                    'last_name',
                    'qr_code_generation',
                    'date_create',
                    'matched_photo')

    list_filter = ('qr_code_generation',
                  'matched_photo')

    search_fields = ('first_name',
                     'last_name')

admin.site.register(Student, StudentAdmin)