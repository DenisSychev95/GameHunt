from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import F, Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Game, Genre, Platform, GameVote, GameComment
from .forms import GameCommentForm
from . utils import get_adult, search_games, paginate_games
import time
from .utils import trailer_embed_url


COMMENT_COOLDOWN_SECONDS = 60


def game_list(request):
    # ---------- Поиск ----------
    # Весь поиск сжимаем в одну строку, все остальное в utils
    games, search_query, genres, platforms,  sort, genre_id, platform_id, min_rating = search_games(request)

    # Если в фильтр поиска приходит id жанра или платформы, преобразуем к числу или возвращаем None
    genre = int(genre_id) if genre_id else None
    platform = int(platform_id) if platform_id else None

    # ---------- Пагинация ----------
    count = 3
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

    rating_choices = list(range(1, 11))

    context = {
        'games': games,
        'custom_range': custom_range,
        'genres': genres,
        'platforms': platforms,
        'current_query': search_query,
        'current_genre': genre,
        'current_platform': platform,
        'min_rating': min_rating,
        'current_sort': sort,
        'extra_query': extra_query,
        'rating_choices': rating_choices,
    }
    return render(request, 'games/game_list.html', context)


def game_detail(request, slug):
    game = get_object_or_404(Game, slug=slug)


    # защита 16+
    is_adult = get_adult(request)
    if game.is_adult_only and not is_adult:
        messages.error(request, 'Эта игра доступна только пользователям 16+.')
        return redirect('game_list')

    # +1 просмотр за сессию
    viewed_games = request.session.get('viewed_games', [])
    if game.id not in viewed_games:
        Game.objects.filter(pk=game.id).update(views_count=F('views_count') + 1)
        viewed_games.append(game.id)
        request.session['viewed_games'] = viewed_games
        request.session.modified = True

    # комментарии (у тебя comment.user, значит related_name вероятно 'comments' и поле user)
    comments = game.comments.filter(is_deleted=False).select_related('user')

    # форма комментария (пустая, отправка идёт в отдельный url)
    form = GameCommentForm()

    # голос пользователя
    user_vote = None
    if request.user.is_authenticated:
        user_vote = GameVote.objects.filter(user=request.user, game=game).first()

    trailer_embed = trailer_embed_url(game.trailer_url)

    context = {
        'game': game,
        'comments': comments,
        'comment_form': form,
        'user_vote': user_vote,
        'trailer_embed': trailer_embed,
    }
    return render(request, 'games/game_detail.html', context)


@login_required
def game_vote(request, slug):
    game = get_object_or_404(Game, slug=slug)

    is_adult = get_adult(request)
    if game.is_adult_only and not is_adult:
        messages.error(request, 'Эта игра доступна только пользователям 16+.')
        return redirect('game_list')

    if request.method != "POST":
        return redirect('game_detail', slug=slug)

    value = request.POST.get("value")
    if value not in ("1", "-1"):
        return redirect('game_detail', slug=slug)

    vote_value = int(value)

    vote, created = GameVote.objects.get_or_create(
        user=request.user, game=game,
        defaults={'value': vote_value}
    )
    if not created and vote.value != vote_value:
        vote.value = vote_value
        vote.save(update_fields=["value"])

    messages.success(request, 'Ваш голос учтён.')
    return redirect('game_detail', slug=slug)


def game_add_comment(request, slug):
    game = get_object_or_404(Game, slug=slug)

    if request.method != 'POST':
        return redirect('game_detail', slug=slug)

    if not request.user.is_authenticated:
        messages.error(request, 'Чтобы комментировать, нужно войти на сайт.')
        return redirect('account_login')

    # --- антиспам: 1 комментарий в минуту ---
    # ключ привязан к пользователю и игре
    key = f'comment_cooldown_game_{game.id}_user_{request.user.id}'
    last_ts = request.session.get(key)

    now = int(time.time())
    if last_ts and (now - int(last_ts)) < COMMENT_COOLDOWN_SECONDS:
        messages.error(request, 'Слишком часто. Можно оставлять комментарий не чаще 1 раза в минуту.')
        return redirect('game_detail', slug=slug)

    form = GameCommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.game = game
        comment.save()

        request.session[key] = now
        request.session.modified = True

        messages.success(request, 'Комментарий добавлен.')
    else:
        messages.error(request, 'Комментарий не отправлен. Проверь текст.')

    return redirect('game_detail', slug=slug)


# Удаление комментариев со страницы игры
@login_required(login_url='account_login')
def game_comment_delete(request, pk):
    # Получаем доступ к нужному комментарию
    comment = get_object_or_404(GameComment, id=pk)
    game = comment.game  # получаем доступ к игре, связанной с комментарием,
    # чтобы потом перенаправить на страницу с этой же игрой

    # Проверяем права:
    # Кто может удалить комментарий - суперпользователь может удалить любой комментарий,
    # автор комментария - может удалять только свои комментарии
    if not (request.user.is_superuser or request.user == comment.user):
        messages.error(request, 'Вы не можете удалить этот комментарий.')
        return redirect('game_detail', slug=game.slug)

    if request.method == 'POST':
        comment.is_deleted = True  # меняем флаг комментария, и он перестает отображаться на странице с игрой,
        # но не удаляется из БД
        # сохраняем изменения в модель
        comment.save()
        messages.success(request, 'Комментарий удалён.')

    # Перенаправляем на страницу с этой же игрой
    return redirect('game_detail', slug=game.slug)


@login_required(login_url='account_login')
def game_comment_edit(request, pk):
    # Получили нужный комментарий из отображенных на странице по его id
    comment = get_object_or_404(GameComment, id=pk, is_deleted=False)
    # получаем доступ к игре, связанной с комментарием,
    # чтобы потом перенаправить на страницу с этой же игрой
    game = comment.game

    # Разрешаем редактировать комментарий только автору комментария
    if comment.user != request.user:
        messages.error(request, 'Вы можете редактировать только свои комментарии.')
        return redirect('game_detail', slug=game.slug)

    if request.method == 'POST':
        form = GameCommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Комментарий обновлён.')
            return redirect('game_detail', slug=game.slug)
    else:
        form = GameCommentForm(instance=comment)

    context = {
        'game': game,
        'comment': comment,
        'form': form,
    }
    return render(request, 'games/comment_edit.html', context)
