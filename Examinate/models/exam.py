from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField


class Exam(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100, null=True)
    grade = models.IntegerField(default=0)
    image = models.FileField(upload_to='exams/pdfs/')
    cover = models.ImageField(upload_to='exams/covers/', null=True, blank=True)

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        self.image.delete()
        self.cover.delete()
        super().delete(*args, **kwargs)


class Question(models.Model):
    question = models.CharField(max_length=1000)
    content = RichTextUploadingField(blank=True, null=True)
    answer = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.question
