from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# Create a custom Admin class for your CustomUser model
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Pass in the list_display from the base UserAdmin and add your custom field
    list_display = ('username', 'email', 'is_staff', 'user_type',)

    # Use a custom form for creating users in the admin
    # This is optional but can be useful for customization
    # form = CustomUserChangeForm
    # add_form = CustomUserCreationForm

    # Define the fieldsets for adding/changing users in the admin
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('user_type',)}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('user_type',)}),
    )

# You should also register your other models here
from .models import GameWord, GameSession, Guess

@admin.register(GameWord)
class GameWordAdmin(admin.ModelAdmin):
    list_display = ('word',)

@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'target_word', 'session_date', 'is_won', 'guesses_count')
    list_filter = ('session_date', 'is_won')

@admin.register(Guess)
class GuessAdmin(admin.ModelAdmin):
    list_display = ('session', 'guessed_word', 'sequence', 'created_at')


# Add a simple admin view for daily report
from django.urls import path
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponse
from django.db.models import Count


def daily_report_view(request):
    from django.shortcuts import render
    today = __import__('datetime').date.today()
    users_played = GameSession.objects.filter(session_date=today).values('user').distinct().count()
    correct = GameSession.objects.filter(session_date=today, is_won=True).count()
    return render(request, 'guess_game_user/admin/daily_report.html', {
        'date': today,
        'users_played': users_played,
        'correct_guesses': correct,
    })


# register the admin view
try:
    original_get_urls = admin.site.get_urls
    def get_urls():
        urls = original_get_urls()
        my_urls = [path('game_reports/daily/', admin.site.admin_view(daily_report_view))]
        return my_urls + urls

    admin.site.get_urls = get_urls
except Exception:
    # If anything goes wrong, don't break admin
    pass
