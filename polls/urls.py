from django.urls import path

from . import views, scan_file_views

app_name = 'polls'
urlpatterns = [
    path('', views.index, name='index'),
    path('<int:question_id>/', views.upload_file, name='file_upload'),
    path('1/poop', scan_file_views.scan_file, name='scan_file'),
]