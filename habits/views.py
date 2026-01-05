from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta, date

from .models import Habit, HabitCompletion
from .forms import HabitForm


@login_required
def dashboard(request):
    today = date.today()
    habits = Habit.objects.filter(user=request.user, is_active=True)

    # ---- Prefetch completions (performance fix) ----
    completions = HabitCompletion.objects.filter(
        habit__user=request.user,
        date__gte=today - timedelta(days=6),
        date__lte=today,
    )

    completed_map = {(c.habit_id, c.date) for c in completions}

    completed_today = {
        c.habit_id for c in completions if c.date == today
    }

    # ---- Total discipline score ----
    total_score = sum(habit.discipline_score() for habit in habits)

    # ---- Daily scores (single source of truth) ----
    daily_scores = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        score = 0

        for habit in habits:
            if (habit.id, day) in completed_map:
                score += habit.discipline_score()

        daily_scores.append({
            "date": day.strftime("%b %d"),
            "score": score,
        })

    # ---- Trend ----
    trend = "stable"
    if daily_scores[-1]["score"] > daily_scores[0]["score"]:
        trend = "improving"
    elif daily_scores[-1]["score"] < daily_scores[0]["score"]:
        trend = "declining"

    # ---- Burnout detection ----
    has_burnout_risk = any(
        habit.burnout_risk() == "high"
        for habit in habits
    )

    # ---- Consistency index (30 days) ----
    total_possible = habits.count() * 30
    completed_30 = HabitCompletion.objects.filter(
        habit__user=request.user,
        date__gte=today - timedelta(days=30),
    ).count()

    consistency_score = int((completed_30 / total_possible) * 100) if total_possible else 0

    context = {
        "habits": habits,
        "completed_habits": completed_today,
        "daily_scores": daily_scores,
        "total_score": int(total_score),
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

    obj, created = HabitCompletion.objects.get_or_create(
        habit=habit,
        date=today,
    )

    if created:
        habit.auto_tune_difficulty()

    return redirect("dashboard")

#