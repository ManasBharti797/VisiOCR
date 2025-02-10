
"""
URL configuration for internship project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
# internship/urls.py
from django.contrib import admin
from django.urls import path, include
from visiocr.views import upload_image  # Import the upload_image view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ocr/', upload_image, name='upload_image'),  # Use your existing view
    path('', upload_image, name='upload_image'),  # Redirect root URL to the upload_image view
    path('ocr/', include('visiocr.urls')),  # Assuming 'visiocr' is your app name
]




