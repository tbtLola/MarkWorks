from django import forms
from .models import Exam


class UploadForms(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ('title', 'author', 'image')
