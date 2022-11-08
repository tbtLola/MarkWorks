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
        exclude = ['author', 'grade', 'cover', 'image', 'user']
        labels = {
            'title': '',
        }
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Enter a title for the assessment'}),
        }

    def __init__(self, *args, **kwargs):
        super(ExamForm, self).__init__(*args, **kwargs)
        # self.fields['title'].label = ""


class StudentAssessmentMarkingForm(forms.ModelForm):
    exam_assessment = forms.ModelChoiceField(label="Item Choices", queryset=Exam.objects.all(), required=True)
    image = forms.FileField()
    class Meta:
        model = exam.StudentAssessment
        fields = ('image', 'exam_assessment')
    def getThing(self, user):
        unfilter = Exam.objects.all()
        all__filter = Exam.objects.all().filter(user=user)
        self.exam_assessment = forms.ModelChoiceField(label="Item Choices", queryset=all__filter, required=True)
        print(all__filter)
        print(unfilter)




class QuestionForm(forms.ModelForm):
    content = RichTextUploadingField()
    answer = forms.CharField(max_length=100)

    class Meta:
        model = Question
        fields = ('content', 'answer', 'question_type')
