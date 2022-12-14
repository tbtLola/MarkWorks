from django.urls import path, re_path, include

from . import views, scan_file_views

app_name = 'Examinate'
urlpatterns = [
    path('', views.index, name='index'),
    path('<int:question_id>/', views.upload_file, name='file_upload'),
    path('1/poop', scan_file_views.scan_file, name='scan_file'),
    re_path(r'^ckeditor/', include('ckeditor_uploader.urls')),
]