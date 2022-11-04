from django import forms
from .models import *
from ckeditor_uploader.fields import RichTextUploadingField


class UploadForms(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ('title', 'author', 'image')


class QuestionForm(forms.ModelForm):
    content = RichTextUploadingField()

    class Meta:
        model = Question
        fields = 'content',
