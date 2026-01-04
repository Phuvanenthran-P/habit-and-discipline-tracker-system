from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta, date

from .models import Habit, HabitCompletion
from .forms import HabitForm


@login_required
def dashboard(request):
    today = date.today()
    habits = Habit.objects.filter(user=request.user)

    completed_today = HabitCompletion.objects.filter(
        habit__user=request.user,
        date=today
    ).values_list("habit_id", flat=True)

    total_score = sum(
        habit.discipline_score()
        for habit in habits
        if habit.is_active
    )

    daily_scores = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        score = 0

        for habit in habits:
            base = habit.weight * habit.priority_multiplier()
            if habit.completions.filter(date=day).exists():
                score += base

        daily_scores.append({
            "date": day.strftime("%b %d"),
            "score": score,
        })

    trend = "stable"
    if daily_scores[-1]["score"] > daily_scores[0]["score"]:
        trend = "improving"
    elif daily_scores[-1]["score"] < daily_scores[0]["score"]:
        trend = "declining"

    # 🔥 CRITICAL FIX — LOGIC BELONGS HERE
    has_burnout_risk = any(
        habit.burnout_risk() == "high"
        for habit in habits
    )

    # Simple consistency index (last 30 days)
    total_possible = habits.count() * 30
    completed = HabitCompletion.objects.filter(
        habit__user=request.user,
        date__gte=today - timedelta(days=30)
    ).count()

    consistency_score = int((completed / total_possible) * 100) if total_possible else 0

    context = {
        "habits": habits,
        "completed_habits": set(completed_today),
        "daily_scores": daily_scores,
        "total_score": total_score,
        "trend": trend,
        "has_burnout_risk": has_burnout_risk,
        "consistency_score": consistency_score,
    }

    return render(request, "habits/dashboard.html", context)


@login_required
def habit_create(request):
    if request.method == "POST":
        form = HabitForm(request.POST)
        if form.is_valid():
            habit = form.save(commit=False)
            habit.user = request.user
            habit.save()
            return redirect("dashboard")
    else:
        form = HabitForm()

    return render(request, "habits/habit_form.html", {"form": form})


@login_required
def habit_update(request, pk):
    habit = get_object_or_404(Habit, pk=pk, user=request.user)

    if request.method == "POST":
        form = HabitForm(request.POST, instance=habit)
        if form.is_valid():
            form.save()
            return redirect("dashboard")
    else:
        form = HabitForm(instance=habit)

    return render(request, "habits/habit_form.html", {"form": form})


@login_required
def habit_delete(request, pk):
    habit = get_object_or_404(Habit, pk=pk, user=request.user)

    if request.method == "POST":
        habit.delete()
        return redirect("dashboard")

    return render(request, "habits/habit_confirm_delete.html", {"habit": habit})


@login_required
def mark_complete(request, pk):
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    today = timezone.now().date()

    HabitCompletion.objects.get_or_create(habit=habit, date=today)
    return redirect("dashboard")
