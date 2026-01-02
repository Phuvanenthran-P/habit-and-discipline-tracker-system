from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class Habit(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='habits'
    )
    name = models.CharField(max_length=100)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    weight = models.PositiveIntegerField(help_text="1 (low impact) to 5 (high impact)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    # ---------- STREAK LOGIC ----------

    def current_streak(self):
        today = timezone.now().date()
        streak = 0
        day = today

        while self.completions.filter(date=day).exists():
            streak += 1
            day -= timedelta(days=1)

        return streak

    def last_completed_date(self):
        last = self.completions.order_by('-date').first()
        return last.date if last else None

    def missed_days(self):
        last_done = self.last_completed_date()
        if not last_done:
            return None

        today = timezone.now().date()
        delta = (today - last_done).days

        return max(0, delta - 1)


class HabitCompletion(models.Model):
    habit = models.ForeignKey(
        Habit,
        on_delete=models.CASCADE,
        related_name='completions'
    )
    date = models.DateField()

    class Meta:
        unique_together = ('habit', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.habit.name} - {self.date}"
