import os
from django.db import models
from django.utils import timezone


# Classe Student :
# ----------------
class Student(models.Model):
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    qr_code_generation = models.BooleanField(default=False, verbose_name="QR Code généré")
    date_create = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    matched_photo = models.CharField(max_length=255, null=True, blank=True, verbose_name="Nom du fichier photo")

    class Meta:
        verbose_name = "Élève"
        verbose_name_plural = "Élèves"
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        """
        Sauvegarde l'élève et génère un QR Code si nécessaire.
        """
        # Vérifie si l'objet est nouveau ou si le QR Code n'a pas encore été généré
        is_new_instance = self.pk is None
        super().save(*args, **kwargs)  # Sauvegarde initiale pour obtenir l'ID

        # Si le QR Code n'a pas encore été généré, on le crée
        if not self.qr_code_generation:
            from CORE.utils.generate_qr_code import generate_qr_code  # Import ici pour éviter la boucle
            # Chemin de sortie pour les QR Codes (peut être adapté)
            output_dir = os.path.join('media', 'qr_codes')

            # Appelle la fonction utilitaire pour générer le QR Code
            success = generate_qr_code(self.id, output_dir)

            if success:
                self.qr_code_generation = True  # Met à jour le statut
                super().save(update_fields=['qr_code_generation'])  # Sauvegarde le champ mis à jour


# Classe Photo :
# --------------

class Photo(models.Model):
    image = models.ImageField(upload_to='photos/')
    file_name = models.CharField(max_length=255, unique=True, default='')  # Stocker le nom du fichier
    uploaded_at = models.DateTimeField(auto_now_add=True)
    fk_id_student = models.ForeignKey(
        'Student',on_delete=models.CASCADE,
        verbose_name="Elève associé",
        null=True,
        blank=True
    )
    crop_x = models.FloatField(default=0)
    crop_y = models.FloatField(default=0)
    crop_width = models.FloatField(default=0)
    crop_height = models.FloatField(default=0)
    crop_lock = models.BooleanField(default=False)

    def __str__(self):
        return self.image.name


