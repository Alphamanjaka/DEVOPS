from django.urls import path
from mymessages import views


urlpatterns = [
    path('', views.home, name='home'),
]
