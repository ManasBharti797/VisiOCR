
from django.db import models

class OCRData(models.Model):
    document_type = models.CharField(max_length=100)
    id_number = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    dob = models.CharField(max_length=10)  # Format: DD/MM/YYYY

    def __str__(self):
        return f"{self.document_type} - {self.id_number}"




