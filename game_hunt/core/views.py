from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from games.models import Game, GameComment
from games.forms import GameAdminForm, GameImageFormSet
from .utils import staff_check


def homepage(request):
    return render(request, 'home.html')


def about(request):
    return render(request, 'core/about.html')


def contacts(request):
    return render(request, 'core/contacts.html')


def privacy_policy(request):
    return render(request, 'core/privacy_policy.html')


# Главная страница админ-панели
@user_passes_test(staff_check)
def admin_dashboard(request):
    games = Game.objects.all().order_by('-created_at')
    users = User.objects.all().select_related('profile').order_by('username')

    context = {
        'games': games,
        'users': users,
    }
    return render(request, 'core/admin_dashboard.html', context)


# Добавление игры
@user_passes_test(staff_check)
def admin_game_create(request):
    if request.method == 'POST':
        form = GameAdminForm(request.POST, request.FILES)
        if form.is_valid():
            game = form.save(commit=False)
            game.views_count = 0
            game.save()

            formset = GameImageFormSet(request.POST, request.FILES, instance=game)
            if formset.is_valid():
                formset.save()
                messages.success(request, 'Игра успешно добавлена.')
                return redirect('admin_dashboard')
        else:
            formset = GameImageFormSet(request.POST, request.FILES)
    else:
        form = GameAdminForm()
        formset = GameImageFormSet()

    return render(request, 'core/admin_game_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Добавить игру',
    })


# Редактирование игры
@user_passes_test(staff_check)
def admin_game_edit(request, pk):
    game = get_object_or_404(Game, pk=pk)
    old_views = game.views_count

    if request.method == 'POST':
        form = GameAdminForm(request.POST, request.FILES, instance=game)
        formset = GameImageFormSet(request.POST, request.FILES, instance=game)

        if form.is_valid() and formset.is_valid():
            game = form.save(commit=False)
            game.views_count = old_views
            game.save()
            formset.save()
            messages.success(request, 'Игра обновлена.')
            return redirect('admin_dashboard')
    else:
        form = GameAdminForm(instance=game)
        formset = GameImageFormSet(instance=game)

    return render(request, 'core/admin_game_form.html', {
        'form': form,
        'formset': formset,
        'title': f'Редактировать игру: {game.title}',
    })


# Удаление игры
@user_passes_test(staff_check)
def admin_game_delete(request, pk):
    game = get_object_or_404(Game, pk=pk)

    if request.method == 'POST':
        title = game.title
        game.delete()
        messages.success(request, f'Игра "{title}" удалена.')
        return redirect('admin_dashboard')
    context = {
        'game': game,
    }
    # Можно сделать простое подтверждение
    return render(request, 'core/admin_game_confirm_delete.html', context)


# Комментарии пользователя игры
@user_passes_test(staff_check)
def admin_user_comments(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    comments = GameComment.objects.filter(user=user).select_related('game').order_by('-created_at')

    context = {
        'user': user,
        'comments': comments}
    return render(request, 'core/admin_user_comments.html', context)


# Бан/разбан пользователя
@user_passes_test(staff_check)
def admin_toggle_ban(request, user_id):
    user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        if user.is_active:
            messages.success(request, f'Пользователь {user.username} разблокирован.')
        else:
            messages.warning(request, f'Пользователь {user.username} заблокирован.')
    return redirect('admin_dashboard')