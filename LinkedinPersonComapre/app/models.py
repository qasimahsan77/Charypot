"""
Definition of models.
"""

from django.db import models

# Create your models here.
class ScrapeData(models.Model):
    Name=models.CharField(max_length=300)
