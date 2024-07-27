from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_and_search, name='upload_and_search'),
    path('file/<int:file_id>/', views.view_file, name='view_file'),
    path('file/<int:file_id>/download/', views.download_file, name='download_file'),
]
