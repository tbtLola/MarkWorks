import datetime

from django.db import models


class Student(models.Model):
    first_name = models.CharField(max_length=100, null=False)
    last_name = models.CharField(max_length=100, null=False)
    student_number = models.CharField(max_length=1000, null=True)
    last_modified = models.DateTimeField(auto_now_add=True)


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
