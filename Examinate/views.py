from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from .registration_form import RegistrationForm
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import ExamForm
from .models import Exam

from django.contrib.auth import get_user_model

User = get_user_model()


class Home(TemplateView):
    template_name = 'home.html'


def delete_exam(request, pk):
    if request.method == 'POST':
        exam = Exam.objects.get(pk=pk)
        exam.delete()
    return redirect('exam_list')


class ExamListView(LoginRequiredMixin, ListView):
    model = Exam
    template_name = 'exam_list.html'
    context_object_name = 'exams'


class UploadExamView(LoginRequiredMixin, CreateView):
    model = Exam
    form_class = ExamForm
    success_url = reverse_lazy('exam_list')
    template_name = 'upload_exam.html'


def signup(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('home')
    else:
        form = RegistrationForm()
    return render(request, 'registration/signup.html', {
        'form': form
    })