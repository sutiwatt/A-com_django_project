from django.urls import path
from . import views

urlpatterns = [
    path('', views.show_location_pickface, name='show_location_pickface'),
]

