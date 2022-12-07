from django.db import models


class Student(models.Model):
    name = models.CharField(max_length=100, null=False)
    student_number = models.CharField(max_length=1000, null=True)


class Classroom(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey("UserProfile", on_delete=models.CASCADE)
    creation_date = models.DateTimeField(auto_now_add=True)


class StudentClass(models.Model):
    classroom = models.ForeignKey("Classroom", on_delete=models.CASCADE)
    student = models.ForeignKey("Student", on_delete=models.CASCADE)


class TeacherClass(models.Model):
    classroom = models.ForeignKey("Classroom", on_delete=models.CASCADE)
    user = models.ForeignKey("UserProfile", on_delete=models.CASCADE)

