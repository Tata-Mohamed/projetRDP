from django.db import models

class ExcelData(models.Model):
    data = models.TextField()