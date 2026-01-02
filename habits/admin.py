from django.contrib import admin
from .models import Habit, HabitCompletion


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'priority', 'weight', 'is_active')
    list_filter = ('priority', 'is_active')
    search_fields = ('name',)
    ordering = ('-created_at',)


@admin.register(HabitCompletion)
class HabitCompletionAdmin(admin.ModelAdmin):
    list_display = ('habit', 'date')
    list_filter = ('date',)
    search_fields = ('habit__name',)
    ordering = ('-date',)
