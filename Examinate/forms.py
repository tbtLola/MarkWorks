from django import forms
from .models import *
from ckeditor_uploader.fields import RichTextUploadingField


class UploadForms(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()


class ExamForm(forms.ModelForm):
    # title = forms.CharField(max_length=50)
    class Meta:
        model = Exam
        exclude = ['author', 'grade', 'image', 'cover', 'user_id']
        labels = {
            'title': '',
        }
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Enter a title for the assessment'}),
        }

    def __init__(self, *args, **kwargs):
        super(ExamForm, self).__init__(*args, **kwargs)
        # self.fields['title'].label = ""


class QuestionForm(forms.ModelForm):
    content = RichTextUploadingField()
    answer = forms.CharField(max_length=100)

    class Meta:
        model = Question
        fields = ('content', 'answer')
