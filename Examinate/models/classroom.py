import datetime

from django.db import models
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image, ImageDraw
import uuid


class Student(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    first_name = models.CharField(max_length=100, null=False)
    last_name = models.CharField(max_length=100, null=False)
    student_number = models.CharField(max_length=1000, null=True)
    qr_code = models.ImageField(upload_to='qr_codes', blank=True)
    last_modified = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.first_name)

    def save(self, **kwargs):
        print(self.id)
        qrcode_img = qrcode.make(self.id)
        canvas = Image.new('RGB', (400, 400), 'white')
        draw = ImageDraw.Draw(canvas)
        canvas.paste(qrcode_img)
        fname = f'qr_code--{self.id}'+'.png'
        buffer = BytesIO()
        canvas.save(buffer, 'PNG')
        self.qr_code.save(fname, File(buffer), save=False)
        canvas.close()
        super().save(kwargs)




class Classroom(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey("UserProfile", on_delete=models.CASCADE)
    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class StudentClass(models.Model):
    classroom = models.ForeignKey("Classroom", on_delete=models.CASCADE)
    student = models.ForeignKey("Student", on_delete=models.CASCADE)


class TeacherClass(models.Model): #TODO not needed
    classroom = models.ForeignKey("Classroom", on_delete=models.CASCADE)
    user = models.ForeignKey("UserProfile", on_delete=models.CASCADE)


class Csv(models.Model):
    file_name = models.FileField(upload_to='csvs')
    upload_time = models.DateTimeField(auto_now_add=True)
    activated = models.BooleanField(default=False)

    def __str__(self):
        return "File id: {self.id"
