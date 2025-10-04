from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ("admin", "Admin"),
        ("player", "Player"),
    )
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default="player"
    )

    def __str__(self):
        return self.username

class GameWord(models.Model):
    word = models.CharField(max_length=5, unique=True)

    def __str__(self):
        return self.word

from django.conf import settings

class GameSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='game_sessions')
    target_word = models.ForeignKey(GameWord, on_delete=models.PROTECT)
    session_date = models.DateField(auto_now_add=True)
    is_won = models.BooleanField(default=False)
    guesses_count = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.user.username} - {self.session_date}'

class Guess(models.Model):
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='guesses')
    guessed_word = models.CharField(max_length=5)
    sequence = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sequence']

    def __str__(self):
        return f'{self.session.user.username} - Guess {self.sequence}: {self.guessed_word}'
