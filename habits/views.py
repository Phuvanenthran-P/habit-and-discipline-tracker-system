from django.shortcuts import render, redirect, get_object_or_404
from .forms import HabitForm
from django.utils import timezone
from datetime import date
from django.contrib.auth.decorators import login_required
from .models import Habit, HabitCompletion

@login_required
def dashboard(request):
    today = date.today()

    habits = Habit.objects.filter(user=request.user)

    completed_today = HabitCompletion.objects.filter(
        habit__user=request.user,
        date=today
    ).values_list("habit_id", flat=True)

    context = {
        "habits": habits,
        "completed_habits": set(completed_today),
    }

    return render(request, "habits/dashboard.html", context)


@login_required
def habit_create(request):
    if request.method == 'POST':
        form = HabitForm(request.POST)
        if form.is_valid():
            habit = form.save(commit=False)
            habit.user = request.user
            habit.save()
            return redirect('dashboard')
    else:
        form = HabitForm()

    return render(request, 'habits/habit_form.html', {'form': form})


@login_required
def habit_update(request, pk):
    habit = get_object_or_404(Habit, pk=pk, user=request.user)

    if request.method == 'POST':
        form = HabitForm(request.POST, instance=habit)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = HabitForm(instance=habit)

    return render(request, 'habits/habit_form.html', {'form': form})


@login_required
def habit_delete(request, pk):
    habit = get_object_or_404(Habit, pk=pk, user=request.user)

    if request.method == 'POST':
        habit.delete()
        return redirect('dashboard')

    return render(request, 'habits/habit_confirm_delete.html', {'habit': habit})


@login_required
def mark_complete(request, pk):
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    today = timezone.now().date()

    HabitCompletion.objects.get_or_create(
        habit=habit,
        date=today
    )

    return redirect('dashboard')
