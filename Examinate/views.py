from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.core.files.storage import FileSystemStorage
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy

from .forms import ExamForm
from .models import Exam
class Home(TemplateView):

    template_name = 'home.html'

def upload(request):
    context = {}

    if request.method == 'POST':
        uploaded_file = request.FILES['examFile']

        fs = FileSystemStorage()
        name = fs.save(uploaded_file.name, uploaded_file)
        url = fs.url(name)
        context['url'] = fs.url(name)

    return render(request, 'upload.html', context)

def delete_exam(request, pk):
    if request.method == 'POST':
        exam = Exam.objects.get(pk=pk)
        exam.delete()
    return redirect('exam_list')

class ExamListView(ListView):
    model = Exam
    template_name = 'exam_list.html'
    context_object_name = 'exams'

class UploadExamView(CreateView):
    model = Exam
    form_class = ExamForm
    success_url = reverse_lazy('exam_list')
    template_name = 'upload_exam.html'