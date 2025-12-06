from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import F, Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Game, Genre, Platform, GameVote, GameComment
from .forms import GameCommentForm
from . utils import get_adult, search_games, paginate_games


def game_list(request):
    # ---------- Поиск ----------
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
    # пытаемся получить доступ к данным сесии пользователя по ключу 'viewed_games', т.к его изначально нет
    # инициализируем пустым списком и кладем в viewed_games
    viewed_games = request.session.get('viewed_games', [])

    # на момент начала сессии пользователя список всегда пуст, ни одна игра туда еще не попала
    if game.id not in viewed_games:
        # у выбранной игры по id не извлекая данных из БД внутри поля views_count увеличиваем его значение на +1
        # при использовании класса F позволяющего осуществлять простые арифметические операции внутри самой БД
        Game.objects.filter(pk=game.id).update(views_count=F('views_count') + 1)
        # после увеличения views_count на +=1 добавляем id игры в viewed_games
        viewed_games.append(game.id)
        # т.к request.session только позволяет получить данные нужно в его ключ 'viewed_games' переприсвоить
        # обновленный массив viewed_games
        request.session['viewed_games'] = viewed_games

    # Для оптимизации числа SQL-запросов получаем за один запрос все неудаленные комментарии и
    # связанные с ними пользователи с помощью select_related
    comments = game.comments.filter(is_deleted=False).select_related('user')

    if request.method == 'POST':
        # при попытке отправки комментария незарегистрированным пользователем - редирект на авторизацию
        if not request.user.is_authenticated:
            messages.error(request, 'Чтобы комментировать, нужно войти на сайт.')
            return redirect('account_login')

        form = GameCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            # четко устанавливаем автора комментария - текущий авторизованный пользователь
            comment.user = request.user
            # присваиваем в поле comment.game объект выше полученной игры
            comment.game = game
            # сохраняем экземпляр GameComment в модель
            comment.save()
            messages.success(request, 'Комментарий добавлен.')
            # редирект на страницу текущей игры
            return redirect('game_detail', slug=game.slug)
    else:
        form = GameCommentForm()

    # Изначально присвоим в голос пользователя None
    user_vote = None
    # Если пользователь авторизован
    if request.user.is_authenticated:
        # Пробуем узнать результат голосования пользователя путем получения первого результата queryset
        # из модели GameVote для вывода на страницу
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

    # защита 18+
    is_adult = get_adult(request)
    # если контент игры 18+ и флаг совершеннолетия False
    # Выводим сообщение об ошибке
    if game.is_adult_only and not is_adult:
        messages.error(request, 'Эта игра доступна только пользователям 18+.')
        # перенаправили на страницу со всеми играми
        return redirect('game_list')

    # если в адресную строку пришло что-то кроме 'like'/'dislike' после slug
    if value not in ('like', 'dislike'):
        # перенаправим на страницу с текущей игрой
        return redirect('game_detail', slug=slug)

    # присвоим в vote_value 1 если выбран- like, -1 - если dislike
    vote_value = 1 if value == 'like' else -1

    # получаем доступ к полю экземпляру модели GameVote по queryset текущего пользователя и текущей игры
    # если created=True- мы создали экземпляр, далее с помощью defaults={'value': vote_value} в его поле поместили
    # текущий голос пользователя
    vote, created = GameVote.objects.get_or_create(user=request.user, game=game, defaults={'value': vote_value})
    # если created=False
    if not created:
        # мы переопределяем результат голосования пользователя, вдруг решение изменено
        vote.value = vote_value
        # сохраняем экземпляр модели GameVote
        vote.save()
    # Выводим сообщение об успешном результате голосования
    messages.success(request, 'Ваш голос учтён.')
    return redirect('game_detail', slug=slug)


@login_required(login_url='account_login')
# Удаление комментариев со страницы игры
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
