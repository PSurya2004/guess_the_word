from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from .forms import PlayerRegistrationForm
from django.contrib.auth.views import LoginView as AuthLoginView
from django.contrib.auth.views import LogoutView as AuthLogoutView
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone
from datetime import date
from django.db.models import Q
import json

from .models import GameWord, GameSession, Guess


@login_required
@ensure_csrf_cookie
def game(request):
    return render(request, 'guess_game_user/game.html')


def register(request):
    if request.method == 'POST':
        form = PlayerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            return redirect('guess_game_user:login')
        else:
            print(form.errors)
    else:
        form = PlayerRegistrationForm()
    return render(request, 'guess_game_user/register.html', {'form': form})


class LoginView(AuthLoginView):
    template_name = 'guess_game_user/login.html'
    success_url = reverse_lazy('guess_game_user:game')


class LogoutView(AuthLogoutView):
    next_page = reverse_lazy('guess_game_user:login')


def do_logout(request):
    """Explicit logout endpoint that logs out the user and redirects to login."""
    logout(request)
    return redirect('guess_game_user:login')


@login_required
def api_new_session(request):
    """
    Start a new game session for the logged-in user.
    Rules: max 3 sessions per user per day.
    Picks a random word from GameWord and creates GameSession.
    Returns JSON: { session_started: bool, message: str }
    """
    # If accessed via browser GET, return a friendly message instead of a 405 page
    if request.method != 'POST':
        return JsonResponse({'message': 'This endpoint is for AJAX POST requests only. Use the game UI to start a session.'})

    user = request.user
    today = date.today()
    sessions_today = GameSession.objects.filter(user=user, session_date=today).count()
    if sessions_today >= 3:
        return JsonResponse({'session_started': False, 'message': 'Daily session limit reached (3 per day).'}, status=403)

    # pick a random GameWord
    try:
        word_qs = GameWord.objects.all()
        total = word_qs.count()
        # If no words are configured, auto-seed a small default list so the app can be used immediately.
        if total == 0:
            default = ['APPLE','BRAVE','CHIEF','DELTA','EAGER','FAITH','GHOST','HOUSE','INPUT','JUICE',
                       'KNIFE','LIGHT','MIGHT','NIGHT','OCEAN','PLANT','QUICK','RIVER','STONE','TRUST']
            for w in default:
                GameWord.objects.get_or_create(word=w)
            word_qs = GameWord.objects.all()
            total = word_qs.count()

        import random
        rnd = random.randint(0, total - 1)
        target_word = word_qs.all()[rnd]

        session = GameSession.objects.create(user=user, target_word=target_word)

        return JsonResponse({'session_started': True, 'session_id': session.id, 'message': 'Session started.', 'words_count': total})
    except Exception as e:
        # return JSON error to the client to aid debugging
        return JsonResponse({'session_started': False, 'message': f'Error starting session: {str(e)}', 'words_count': 0}, status=500)


@login_required
def api_guess(request):
    """
    Process a guess from the user for their active (today's last) session.
    Expects JSON: { guessed_word: 'ABCDE' }
    Returns JSON: { colors: [0|1|2,...], is_correct: bool, guesses_left: int, target_word: 'WORD' }
    """
    # If accessed via browser GET, return a friendly message instead of a 405 page
    if request.method != 'POST':
        return JsonResponse({'message': 'This endpoint is for AJAX POST requests only. Submit guesses via the game UI.'})

    user = request.user
    payload = json.loads(request.body.decode('utf-8'))
    guessed_word = payload.get('guessed_word', '').upper()

    if len(guessed_word) != 5 or not guessed_word.isalpha():
        return JsonResponse({'message': 'Guessed word must be 5 letters.'}, status=400)

    # find the latest session for user today that is not finished
    today = date.today()
    session = GameSession.objects.filter(user=user, session_date=today, guesses_count__lt=5, is_won=False).order_by('-id').first()
    if not session:
        # maybe none exists, deny
        return JsonResponse({'message': 'No active session. Start a new game.'}, status=403)

    # enforce guesses per session
    if session.guesses_count >= 5:
        return JsonResponse({'message': 'No more guesses allowed for this session.'}, status=403)

    target = session.target_word.word.upper()

    # compute colors per letter: 2 correct pos, 1 present wrong pos, 0 absent
    colors = [0] * 5
    target_letters = list(target)
    guess_letters = list(guessed_word)

    # first pass for exact matches
    for i in range(5):
        if guess_letters[i] == target_letters[i]:
            colors[i] = 2
            target_letters[i] = None  # consume

    # second pass for present but wrong position
    for i in range(5):
        if colors[i] == 0 and guess_letters[i] in target_letters:
            colors[i] = 1
            # consume the first occurrence
            idx = target_letters.index(guess_letters[i])
            target_letters[idx] = None

    # save the guess
    guess_seq = session.guesses.count() + 1
    Guess.objects.create(session=session, guessed_word=guessed_word, sequence=guess_seq)

    # update session
    session.guesses_count += 1
    if guessed_word == target:
        session.is_won = True
    session.save()

    guesses_left = max(0, 5 - session.guesses_count)

    resp = {'colors': colors, 'is_correct': session.is_won, 'guesses_left': guesses_left}
    # only reveal the target word when the game is finished
    if session.is_won or guesses_left <= 0:
        resp['target_word'] = session.target_word.word

    return JsonResponse(resp)


@require_GET
@login_required
def api_report_day(request):
    """Admin report: number of users who played today and number of correct guesses today."""
    if not request.user.is_superuser:
        return JsonResponse({'message': 'Forbidden'}, status=403)
    today = date.today()
    from django.db.models import Count, Q
    users_played = GameSession.objects.filter(session_date=today).values('user').distinct().count()
    correct = GameSession.objects.filter(session_date=today, is_won=True).count()
    return JsonResponse({'date': str(today), 'users_played': users_played, 'correct_guesses': correct})


@require_GET
@login_required
def api_report_user(request, username):
    """Admin report for a user: date, number of words tried and number of correct guesses."""
    # only admin can query arbitrary users
    if not request.user.is_superuser:
        return JsonResponse({'message': 'Forbidden'}, status=403)
    from django.db.models import Count
    sessions = GameSession.objects.filter(user__username=username).values('session_date').annotate(words_tried=Count('id'), correct=Count('id', filter=Q(is_won=True))).order_by('-session_date')
    return JsonResponse({'user': username, 'report': list(sessions)})


@require_GET
@login_required
def api_report_me(request):
    """Return the calling user's report (date, words tried, correct) - for players to view their own games."""
    from django.db.models import Count
    username = request.user.username
    sessions = GameSession.objects.filter(user=request.user).values('session_date').annotate(words_tried=Count('id'), correct=Count('id', filter=Q(is_won=True))).order_by('-session_date')
    return JsonResponse({'user': username, 'report': list(sessions)})
