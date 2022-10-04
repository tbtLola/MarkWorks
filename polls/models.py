from django.db import models

# Create your models here.

class Exam (models.Model):
    exam_id = models.AutoField(primary_key=True)
    exam_name = models.CharField(max_length=50)
    exam_photo_name = models.CharField(max_length=500)
    exam_score = models.IntegerField()