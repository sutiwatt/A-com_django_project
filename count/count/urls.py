from django.urls import include, path

urlpatterns = [
    # Other URL patterns
    path('', include('check_location.url')),
]
