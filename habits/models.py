from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    daily_load_cap = models.IntegerField(default=10)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


class Habit(models.Model):
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("normal", "Normal"),
        ("hard", "Hard"),
    ]

    IDENTITY_CHOICES = [
        ("body", "Body"),
        ("mind", "Mind"),
        ("craft", "Skill / Craft"),
        ("discipline", "Discipline"),
        ("recovery", "Recovery"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="habits")
    identity = models.CharField(max_length=20, choices=IDENTITY_CHOICES, default="discipline")
    name = models.CharField(max_length=100)

    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="low")
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default="normal")

    weight = models.PositiveIntegerField(help_text="1 (low) to 5 (high)")
    is_active = models.BooleanField(default=True)

    momentum = models.FloatField(default=0.0)
    last_activity = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    # ---------------- STREAKS ----------------

    def current_streak(self):
        today = timezone.now().date()
        streak = 0
        day = today

        while self.completions.filter(date=day).exists():
            streak += 1
            day -= timedelta(days=1)

        return streak

    def effective_streak(self):
        if self.momentum >= 50:
            return self.current_streak() + 2
        if self.momentum >= 25:
            return self.current_streak() + 1
        return self.current_streak()

    def streak_percentage(self):
        return min(self.effective_streak() * 10, 100)

    def last_completed_date(self):
        last = self.completions.order_by("-date").first()
        return last.date if last else None

    def missed_days(self):
        last = self.last_completed_date()
        if not last:
            return 0
        delta = (timezone.now().date() - last).days
        return max(0, delta - 1)

    # ---------------- LOAD & SCORING ----------------

    def priority_multiplier(self):
        return {"low": 1, "medium": 2, "high": 3}.get(self.priority, 1)

    def difficulty_multiplier(self):
        return {"easy": 0.8, "normal": 1.0, "hard": 1.3}.get(self.difficulty, 1.0)

    def load_cost(self):
        base = {"easy": 1, "normal": 2, "hard": 3}.get(self.difficulty, 2)
        return base * self.priority_multiplier()

    def discipline_score(self):
        return self.weight * self.priority_multiplier() * self.difficulty_multiplier()

    # ---------------- INTELLIGENCE ----------------

    def burnout_risk(self):
        if self.load_cost() >= 6 and self.momentum >= 70:
            return "high"
        return "normal"

    def gain_momentum(self):
        gain = (
            self.weight
            * self.priority_multiplier()
            * self.difficulty_multiplier()
        )
        self.momentum += gain
        self.last_activity = timezone.now().date()
        self.save(update_fields=["momentum", "last_activity"])

    def decay_momentum(self):
        if not self.last_activity:
            return

        days_inactive = (timezone.now().date() - self.last_activity).days
        if days_inactive <= 0:
            return

        decay_rate = 0.15
        decay = self.momentum * decay_rate * days_inactive
        self.momentum = max(0, self.momentum - decay)

        self.save(update_fields=["momentum"])

    def auto_tune_difficulty(self):
        old = self.difficulty

        if self.momentum >= 80:
            self.difficulty = "hard"
        elif self.momentum >= 40:
            self.difficulty = "normal"
        else:
            self.difficulty = "easy"

        if self.difficulty != old:
            self.save(update_fields=["difficulty"])


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
