
from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_image, name='upload_image'),
    path('', views.upload_image, name='upload_image'), 
    path('download/', views.download_pdf, name='download_pdf'),
]
