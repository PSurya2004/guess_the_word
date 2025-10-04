from django.urls import path
from . import views

app_name = 'guess_game_user'

urlpatterns = [
    path('game/', views.game, name='game'),
    path('', views.register, name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    # route logout to the explicit view that handles GET/POST and redirects
    path('logout/', views.do_logout, name='logout'),
    path('do-logout/', views.do_logout, name='do_logout'),
    # API endpoints used by frontend JS
    path('api/new-session/', views.api_new_session, name='api_new_session'),
    path('api/guess/', views.api_guess, name='api_guess'),
    path('api/report/day/', views.api_report_day, name='api_report_day'),
    path('api/report/user/<str:username>/', views.api_report_user, name='api_report_user'),
    path('api/report/me/', views.api_report_me, name='api_report_me'),
]