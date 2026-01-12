from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import F, Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Game, Genre, Platform, GameVote, GameComment
from .forms import GameCommentForm
from . utils import get_adult, search_games, paginate_games
import time
from django.utils import timezone
from datetime import timedelta
from .utils import trailer_embed_url
from django.http import JsonResponse
from django.template.loader import render_to_string
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
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"error": "adult_only"}, status=403)
        messages.error(request, 'Эта игра доступна только пользователям 16+.')
        return redirect('game_list')

    if request.method != "POST":
        return redirect('game_detail', slug=slug)

    value = request.POST.get("value")
    if value not in ("1", "-1"):
        return redirect('game_detail', slug=slug)

    vote_value = int(value)

    vote, created = GameVote.objects.update_or_create(
        user=request.user,
        game=game,
        defaults={"value": vote_value},
    )

    # ⬇️ ВОТ КЛЮЧЕВОЕ
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "value": vote_value,
        })

    messages.success(request, 'Ваш голос учтён.')
    return redirect('game_detail', slug=slug)


@login_required
@require_POST
def game_add_comment(request, slug):
    game = get_object_or_404(Game, slug=slug)

    text = request.POST.get("text", "").strip()
    if not text:
        return JsonResponse({"error": "Комментарий пустой"}, status=400)

    # 🔴 ОГРАНИЧЕНИЕ: 1 комментарий в минуту
    last_comment = (
        GameComment.objects
        .filter(user=request.user)
        .order_by("-created_at")
        .first()
    )

    if last_comment:
        delta = timezone.now() - last_comment.created_at
        if delta < timedelta(minutes=1):
            seconds_left = 60 - int(delta.total_seconds())
            return JsonResponse({
                "error": f"Можно комментировать раз в минуту. Подождите {seconds_left} сек."
            }, status=429)

    comment = GameComment.objects.create(
        game=game,
        user=request.user,
        text=text
    )

    # ✔️ ВОЗВРАЩАЕМ HTML КОММЕНТАРИЯ
    html = render_to_string(
        "reviews/partials/review_comment.html",
        {"comment": comment, "user": request.user},
        request=request
    )

    return JsonResponse({
        "success": True,
        "html": html
    })


# Удаление комментариев со страницы игры
@login_required(login_url='account_login')
def game_comment_delete(request, pk):
    comment = get_object_or_404(GameComment, id=pk)
    game = comment.game

    if not (request.user.is_superuser or request.user == comment.user):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "error": "Нет прав на удаление"}, status=403)
        messages.error(request, "Вы не можете удалить этот комментарий.")
        return redirect("game_detail", slug=game.slug)

    if request.method != "POST":
        return redirect("game_detail", slug=game.slug)

    comment.is_deleted = True
    comment.save(update_fields=["is_deleted"])

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "comment_id": pk})

    messages.success(request, "Комментарий удалён.")
    return redirect("game_detail", slug=game.slug)


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
            comment = form.save(commit=False)
            comment.is_edited = True
            comment.save()
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
