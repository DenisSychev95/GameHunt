from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F
from games.utils import paginate_games
from .models import Review
from .forms import ReviewForm, ReviewImageFormSet
from games.models import Game
from django.http import HttpResponseForbidden


def review_list(request):

    qs = Review.objects.select_related("game", "author").filter(is_published=True)

    sort = request.GET.get("sort", "new")
    if sort == "popular":
        qs = qs.order_by("-views_count", "-created_at")
    elif sort == "rating":
        qs = qs.order_by("-rating", "-created_at")
    else:
        qs = qs.order_by("-created_at")

    # пагинация
    page_obj, custom_range = paginate_games(request, qs, 2)  # или твой paginate_queryset
    params = request.GET.copy()
    params.pop("page", None)
    extra_query = params.urlencode()

    return render(request, "reviews/review_list.html", {
        "reviews": page_obj,
        "custom_range": custom_range,
        "extra_query": extra_query,
        "current_sort": sort,
    })


def review_detail(request, pk):
    """
    Одна страница обзора.
    """
    review = get_object_or_404(
        Review.objects.select_related('game', 'author'),
        pk=pk,
        is_published=True
    )
    # увеличиваем счетчик просмотров в пределах одной сессии только на один
    # пытаемся получить доступ к данным сесии пользователя по ключу 'viewed_reviews', т.к его изначально нет
    # инициализируем пустым списком и кладем в viewed_reviews
    viewed_reviews = request.session.get('viewed_reviews', [])

    # на момент начала сессии пользователя список всегда пуст, ни один обзор туда еще не попал
    if review.id not in viewed_reviews:
        # у выбранного обзора по id не извлекая данных из БД внутри поля views_count увеличиваем его значение на +1
        # при использовании класса F позволяющего осуществлять простые арифметические операции внутри самой БД
        Review.objects.filter(pk=review.id).update(views_count=F('views_count') + 1)
        # после увеличения views_count на +=1 добавляем id игры в viewed_reviews
        viewed_reviews.append(review.id)
        # т.к request.session только позволяет получить данные нужно в его ключ 'viewed_reviews' переприсвоить
        # обновленный массив viewed_reviews
        request.session['viewed_reviews'] = viewed_reviews
    context = {
        'review': review,
    }
    return render(request, 'reviews/review_detail.html', context)


@login_required
def review_create(request, game_slug):
    game = get_object_or_404(Game, slug=game_slug)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        # ВАЖНО: для картинок нужен request.FILES
        formset = ReviewImageFormSet(request.POST, request.FILES)

        if form.is_valid() and formset.is_valid():
            review = form.save(commit=False)
            review.game = game
            review.author = request.user
            review.save()

            formset.instance = review
            formset.save()

            messages.success(request, "Обзор создан.")
            return redirect("review_detail", pk=review.pk)
    else:
        form = ReviewForm()
        formset = ReviewImageFormSet()

    return render(request, "reviews/review_form.html", {
        "game": game,
        "form": form,
        "formset": formset,
    })


@login_required
def review_edit(request, pk):
    review = get_object_or_404(Review, pk=pk)

    if review.author != request.user:
        return HttpResponseForbidden("Вы не можете редактировать этот обзор.")

    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        formset = ReviewImageFormSet(request.POST, request.FILES, instance=review)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Обзор обновлён.")
            return redirect("review_detail", pk=review.pk)
    else:
        form = ReviewForm(instance=review)
        formset = ReviewImageFormSet(instance=review)

    return render(request, "reviews/review_form.html", {
        "game": review.game,
        "form": form,
        "formset": formset,
        "review": review,
    })


@login_required
def review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk)
    if review.author != request.user:
        return HttpResponseForbidden("Вы не можете удалить этот обзор.")

    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Обзор удалён.')
        return redirect('review_list')

    return render(request, 'reviews/review_confirm_delete.html', {'review': review})