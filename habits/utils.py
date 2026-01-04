def user_consistency_score(habits, days=30):
    active_habits = habits.filter(is_active=True)

    if not active_habits.exists():
        return 0

    scores = [
        habit.consistency_index(days)
        for habit in active_habits
    ]

    return round(sum(scores) / len(scores), 1)
