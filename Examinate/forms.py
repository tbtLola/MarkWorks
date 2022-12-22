from ckeditor_uploader.fields import RichTextUploadingField
from crispy_forms_gds.helper import FormHelper
from django import forms

from .models import *


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
        all__filter = Exam.objects.all().filter(user=user)
        self.fields['exam_assessment'] = forms.ModelChoiceField(label="Item Choices", queryset=all__filter,
                                                                required=True)

    def __init__(self, *args, **kwargs):
        super(StudentAssessmentMarkingForm, self).__init__(*args, **kwargs)
        # self.fields['title'].label = ""


class QuestionForm(forms.ModelForm):
    content = RichTextUploadingField()
    answer = forms.CharField(max_length=100)

    class Meta:
        model = Question
        fields = ('content', 'answer', 'question_type')


class MarkSheetForm(forms.ModelForm):
    number_of_questions = forms.IntegerField()
    number_of_choices = forms.IntegerField() #TODO put a cap of 7 on this
    classroom = forms.ModelChoiceField(label="Select a class", queryset=Classroom.objects.all(), required=True)

    def get_teacher_class(self, user):
        class_filtered_by_teacher = Classroom.objects.all().filter(user=user)
        self.fields['classroom'] = forms.ModelChoiceField(label='Select a class', queryset=class_filtered_by_teacher, required=True)

    class Meta:
        model = MarkSheet
        fields = ('number_of_questions', 'number_of_choices', 'classroom',)


class CsvModelForm(forms.ModelForm):
    file_name = forms.FileField( label="",
        help_text="Select the CSV file to upload.",
                                 required=False
      )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.form_class = 'crispy_forms.helper.FormHelper'
        self.helper.form_tag = False

    class Meta:
        model = Csv
        fields = ('file_name',)

class StudentEditForm(forms.ModelForm):
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    student_number = forms.CharField(required=False)

    class Meta:
        model = Student
        fields = '__all__'