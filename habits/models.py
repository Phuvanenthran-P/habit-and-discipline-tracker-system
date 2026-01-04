from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class Habit(models.Model):
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="habits")
    name = models.CharField(max_length=100)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="low")
    weight = models.PositiveIntegerField(help_text="1 (low) to 5 (high)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    # ---------- CORE LOGIC ----------

    def current_streak(self):
        today = timezone.now().date()
        streak = 0
        day = today

        while self.completions.filter(date=day).exists():
            streak += 1
            day -= timedelta(days=1)

        return streak

    def last_completed_date(self):
        last = self.completions.order_by("-date").first()
        return last.date if last else None

    def missed_days(self):
        last = self.last_completed_date()
        if not last:
            return 0

        delta = (timezone.now().date() - last).days
        return max(0, delta - 1)

    def priority_multiplier(self):
        mapping = {
            "low": 1,
            "medium": 2,
            "high": 3,
        }
        return mapping.get(self.priority, 1)

    def discipline_score(self):
        base = self.weight * self.priority_multiplier()
        score = (self.current_streak() * base) - (self.missed_days() * base)
        return max(score, 0)

    # ---------- STAGE 11 INTELLIGENCE ----------

    def burnout_risk(self):
        if self.priority == "high" and self.weight >= 4 and self.current_streak() >= 10:
            return "high"
        return "normal"

    def insight_label(self):
        streak = self.current_streak()
        missed = self.missed_days()

        if streak >= 14:
            return "Elite consistency"
        if missed >= 3:
            return "Needs recovery"
        return "On track"

    def streak_percentage(self):
        return min(self.current_streak() * 10, 100)


class HabitCompletion(models.Model):
    habit = models.ForeignKey(
        Habit, on_delete=models.CASCADE, related_name="completions"
    )
    date = models.DateField()

    class Meta:
        unique_together = ("habit", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.habit.name} - {self.date}"
