from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('habits/create/', views.habit_create, name='habit_create'),
    path('habits/<int:pk>/edit/', views.habit_update, name='habit_update'),
    path('habits/<int:pk>/delete/', views.habit_delete, name='habit_delete'),
]
