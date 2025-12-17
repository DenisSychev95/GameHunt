from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils.text import slugify
from django.db.models import F
from games.utils import paginate_games
from .models import Walkthrough
from games.models import Game
from .forms import WalkthroughForm


def walkthrough_list(request):
    qs = Walkthrough.objects.select_related("game", "author").filter(is_published=True)

    sort = request.GET.get("sort", "new")
    if sort == "popular":
        qs = qs.order_by("-views_count", "-created_at")
    else:
        qs = qs.order_by("-created_at")

    page_obj, custom_range = paginate_games(request, qs, 2)
    params = request.GET.copy()
    params.pop("page", None)
    extra_query = params.urlencode()

    return render(request, "walkthroughs/walkthrough_list.html", {
        "walkthroughs": page_obj,
        "custom_range": custom_range,
        "extra_query": extra_query,
        "current_sort": sort,
    })


def walkthrough_detail(request, slug):
    walkthrough = get_object_or_404(
        Walkthrough.objects.select_related('game', 'author'),
        slug=slug,
        is_published=True
    )

    # увеличиваем счетчик просмотров в пределах одной сессии только на один
    # пытаемся получить доступ к данным сесии пользователя по ключу 'viewed_walkthrough', т.к его изначально нет
    # инициализируем пустым списком и кладем в viewed_walkthrough
    viewed_walkthrough = request.session.get('viewed_walkthrough', [])

    # на момент начала сессии пользователя список всегда пуст, ни одно прохождение туда еще не попало
    if walkthrough.id not in viewed_walkthrough:
        # у выбранного обзора по id не извлекая данных из БД внутри поля viewed_walkthrough
        # увеличиваем его значение на +1
        # при использовании класса F позволяющего осуществлять простые арифметические операции внутри самой БД
        Walkthrough.objects.filter(pk=walkthrough.id).update(views_count=F('views_count') + 1)
        # после увеличения views_count на +=1 добавляем id игры в viewed_walkthrough
        viewed_walkthrough.append(walkthrough.id)
        # т.к request.session только позволяет получить данные нужно в его ключ 'viewed_walkthrough' переприсвоить
        # обновленный массив viewed_walkthrough
        request.session['viewed_walkthrough'] = viewed_walkthrough
    return render(request, 'walkthroughs/walkthrough_detail.html', {'walkthrough': walkthrough})


@login_required
def walkthrough_create(request, game_slug):
    game = get_object_or_404(Game, slug=game_slug)

    if request.method == 'POST':
        form = WalkthroughForm(request.POST)
        if form.is_valid():
            walkthrough = form.save(commit=False)
            walkthrough.game = game
            walkthrough.author = request.user
            # простой slug
            base_slug = slugify(form.cleaned_data['title'])[:200]
            slug = base_slug
            counter = 1
            while Walkthrough.objects.filter(slug=slug).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            walkthrough.slug = slug
            walkthrough.save()
            messages.success(request, 'Прохождение добавлено.')
            return redirect('walkthrough_detail', slug=walkthrough.slug)
    else:
        form = WalkthroughForm()

    return render(request, 'walkthroughs/walkthrough_form.html', {'form': form, 'game': game})