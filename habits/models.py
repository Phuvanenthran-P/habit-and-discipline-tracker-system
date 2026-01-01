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
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES
    )
    weight = models.PositiveIntegerField(help_text="1 (low impact) to 5 (high impact)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class HabitLog(models.Model):
    habit = models.ForeignKey(
        Habit,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    date = models.DateField()
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('habit', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.habit.name} - {self.date}"


class HabitCompletion(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)

    class Meta:
        unique_together = ('habit', 'date')

    def __str__(self):
        return f"{self.habit.name} - {self.date}"

def current_streak(self):
    today = timezone.now().date()
    streak = 0
    day = today

    while HabitCompletion.objects.filter(habit=self, date=day).exists():
        streak += 1
        day -= timedelta(days=1)

    return streak

def last_completed_date(self):
    completion = self.completions.order_by('-date').first()
    return completion.date if completion else None

def missed_days(self):
    last_done = self.last_completed_date()
    if not last_done:
        return None

    today = timezone.now().date()
    delta = (today - last_done).days

    if delta <= 1:
        return 0

    return delta - 1