from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField


class Exam(models.Model):
    title = models.CharField(max_length=100)
    user = models.ForeignKey("UserProfile", on_delete=models.CASCADE)
    author = models.CharField(max_length=100, null=True)
    grade = models.IntegerField(default=0)
    image = models.FileField(upload_to='exams/pdfs/', null=True)
    cover = models.ImageField(upload_to='exams/covers/', null=True, blank=True)

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        self.image.delete()
        self.cover.delete()
        super().delete(*args, **kwargs)


QUESTION_TYPES = (
    ('MC', 'Multiple Choice'),
    ('WR', 'Written'),
    ('NU', 'Numerical')
)


class Question(models.Model):
    question = models.CharField(max_length=1000)
    exam = models.ForeignKey("Exam", on_delete=models.CASCADE)
    question_number = models.CharField(max_length=1000, null=True)
    question_type = models.CharField(max_length=255, choices=QUESTION_TYPES, null=True)
    content = RichTextUploadingField(blank=True, null=True)
    answer = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.question


class StudentAssessment(models.Model):
    user = models.ForeignKey("UserProfile", on_delete=models.CASCADE)
    grade = models.IntegerField(null=True)
    assessment_date = models.DateTimeField(auto_now_add=True) #TODO eventually get this from scantron
    image = models.FileField(upload_to='exams/pdfs/', null=True)
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user
