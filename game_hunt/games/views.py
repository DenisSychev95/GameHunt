from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import F, Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Game, Genre, Platform, GameVote
from .forms import GameCommentForm
from . utils import get_adult, search_games, paginate_games


def game_list(request):
    # ---------- Поиск  ----------
    # Весь поиск сжимаем в одну строку, все остальное в utils
    games, search_query, genres, platforms,  sort, genre_id, platform_id = search_games(request)

    # Если в фильтр поиска приходит id жанра или платформы, преобразуем к числу или возвращаем None
    genre = int(genre_id) if genre_id else None
    platform = int(platform_id) if platform_id else None

    # ---------- Пагинация ----------
    count = 1
    # Возвращаем games(объект Page)- итерируемый объект по которому можно пройтись в цикле и получить игры и
    # кастомный диапазон пагинации
    # Не стоит дублировать код и писать page_games= games.object_list(тут уже page_games- массив игр)
    games, custom_range = paginate_games(request, games, count)

    # ---- Формируем в адресной строке строку из query-параметров ----
    params = request.GET.copy()
    if 'page' in params:
        del params['page']
        # Формируем extra_query
    extra_query = params.urlencode()  # например: "search=шутер&genre=1&sort=new"

    context = {
        'games': games,
        'custom_range': custom_range,
        'genres': genres,
        'platforms': platforms,
        'current_query': search_query,
        'current_genre': genre,
        'current_platform': platform,
        'current_sort': sort,
        'extra_query': extra_query
    }
    return render(request, 'games/game_list.html', context)


def game_detail(request, slug):
    game = get_object_or_404(Game, slug=slug)

    # защита 18+
    is_adult = get_adult(request)
    if game.is_adult_only and not is_adult:
        messages.error(request, 'Эта игра доступна только пользователям 18+.')
        return redirect('game_list')

    # увеличиваем счетчик просмотров в пределах одной сессии только на один
    viewed_games = request.session.get('viewed_games', [])

    if game.pk not in viewed_games:
        Game.objects.filter(pk=game.pk).update(views_count=F('views_count') + 1)
        viewed_games.append(game.pk)
        request.session['viewed_games'] = viewed_games


    # комментарии
    comments = game.comments.filter(is_deleted=False).select_related('user')

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Чтобы комментировать, нужно войти на сайт.')
            return redirect('account_login')

        form = GameCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.game = game
            comment.save()
            messages.success(request, 'Комментарий добавлен.')
            return redirect('game_detail', slug=game.slug)
    else:
        form = GameCommentForm()

    # если пользователь авторизован — определим, как он проголосовал
    user_vote = None
    if request.user.is_authenticated:
        user_vote = GameVote.objects.filter(user=request.user, game=game).first()

    context = {
        'game': game,
        'comments': comments,
        'comment_form': form,
        'user_vote': user_vote,
    }
    return render(request, 'games/game_detail.html', context)


@login_required
def game_vote(request, slug, value):
    game = get_object_or_404(Game, slug=slug)

    # защита 18+ на всякий случай
    if game.is_adult_only and (not hasattr(request.user, 'profile') or not request.user.profile.is_adult):
        messages.error(request, 'Эта игра доступна только пользователям 18+.')
        return redirect('game_detail', slug=slug)

    if value not in ('like', 'dislike'):
        return redirect('game_detail', slug=slug)

    vote_value = 1 if value == 'like' else -1

    vote, created = GameVote.objects.get_or_create(user=request.user, game=game, defaults={'value': vote_value})
    if not created:
        # если уже голосовал — обновим значение
        vote.value = vote_value
        vote.save()

    messages.success(request, 'Ваш голос учтён.')
    return redirect('game_detail', slug=slug)