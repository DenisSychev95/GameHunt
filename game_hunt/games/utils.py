from .models import Game, Genre, Platform
from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage


def search_games(request):
    # Для минимизации числа запросов базовый поиск всех игр с подгрузкой жанров и платформ
    games = Game.objects.all().prefetch_related('genres', 'platforms')

    # Получаем все жанры для поиска по жанрам
    genres = Genre.objects.all()
    # Получаем все платформы для поиска по платформам
    platforms = Platform.objects.all()

    # Получаем из своего метода сведения о совершеннолетии пользователя
    is_adult = get_adult(request)
    # Если пользователь несовершеннолетний не выводим контент 18+
    if is_adult is False:
        games = games.filter(is_adult_only=False)

    # Переходим к поиску
    # В результат поиска кладем value из name 'search', если ничего не пришло кладем пустую строку.
    # Удаляем все лишние пробелы
    search_query = request.GET.get('search', '').strip()
    if search_query:
        # Производим поиск и ранее полученных игр
        games = games.filter(
            # поиск по названию игры(регистронезависимый поиск подстроки в полях title модели Game)
            Q(title__icontains=search_query) |
            # или поиск по описанию игры(регистронезависимый поиск подстроки в полях description модели Game)
            Q(description__icontains=search_query) |
            # или поиск по названию жанров по прямой связи в модели Genre
            Q(genres__name__icontains=search_query)
        )

    # Дополнительный фильтр поиска по жанрам: value из name 'genre', если ничего не выбрано поиск по всем жанрам.
    genre_id = request.GET.get('genre')
    if genre_id:
        games = games.filter(genres__id=genre_id)

    # Дополнительный фильтр поиска по платформам: value из name 'genre'
    # если ничего не выбрано поиск по всем платформам.
    platform_id = request.GET.get('platform')
    if platform_id:
        games = games.filter(platforms__id=platform_id)

    # СОРТИРОВКА
    # Дополнительная настройка определяет порядок выведения игр если по умолчанию ничего не выбрано в name 'sort':
    # идет сортировка по дате добавления игры, если в name пришло 'popular'- сортируем по количеству просмотров
    sort = request.GET.get('sort', 'new')

    if sort == 'popular':
        games = games.order_by('-views_count', '-id')
    else:
        games = games.order_by('-created_at', '-id')

    # Избавляемся от дублирования из-за JOIN по жанрам/платформам -distinct.
    games = games.distinct()

    # Возвращаем найденный список игр
    return games, search_query, genres, platforms,  sort, genre_id, platform_id


# Получаем флаг 18+
def get_adult(request):
    # получаем текущего пользователя
    user = request.user
    # по умолчанию ставим присвоим флагу False
    is_adult = False
    # проверим авторизирован ли пользователь, есть ли у него связанный profile по OneToOneField
    # или это суперпользователь
    if user.is_superuser:
        is_adult = True
        return is_adult
    if user.is_authenticated and hasattr(user, 'profile'):
        # забираем значение флага непосредственно из профиля нашего пользователя
        is_adult = user.profile.is_adult
    # вернем значение флага
    return is_adult


# Пагинация игр
def paginate_games(request, games, count):
    page = request.GET.get('page')
    # Создаем экземпляр класса Paginator в него передаем найденные ранее игры и желаемое количество игр на странице
    paginator = Paginator(games, count)
    try:
        # Формируем выводимые на страницу игры исходя из номера страницы
        view_games = paginator.page(page)
    # Если случайно в адресную строку после page= пришло значение, которое невозможно преобразовать к int
    except PageNotAnInteger:
        page = 1
        view_games = paginator.page(page)
    # Обрабатываем переход на несуществующую страницу
    except EmptyPage:
        # Присваиваем номер последней страницы в page
        page = paginator.num_pages
        view_games = paginator.page(page)

    left_index = int(page) - 4
    if left_index < 1:
        left_index = 1

    right_index = int(page) + 5
    if right_index > paginator.num_pages:
        right_index = paginator.num_pages + 1

    custom_range = range(left_index, right_index)
    # Возвращаем объект Page, кастомный диапазон для пагинации
    return view_games, custom_range
