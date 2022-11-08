"""djangoProject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static

from Examinate import views

urlpatterns = [

    # Exam page
    path('', views.Home.as_view(), name='home'),
    path('exams/', views.ExamListView.as_view(), name='exam_list'),
    path('exams/upload', views.UploadExamView.as_view(), name='upload_exam'),
    path('exams/mark_student', views.AssessStudentExamView.as_view(), name='mark_assessment'),

    path('exams/create', views.CreateExamView.as_view(), name='create_exam'),
    path('exams/<int:pk>/', views.delete_exam, name='delete_exam'),
    path('exams/<int:pk>/mark', views.mark_exam, name='mark_exam'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),

    path('add_question/', views.AddQuestionView.as_view(), name='add_question'),
    re_path(r'^ckeditor/', include('ckeditor_uploader.urls')),

    # Sign up page
    path('signup/', views.signup, name='signup'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)