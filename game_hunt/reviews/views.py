from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Review
from .forms import ReviewForm
from games.models import Game
from django.http import HttpResponseForbidden


def review_list(request):
    """
    Список обзоров. Можно отфильтровать по игре:
    /reviews/?game=<slug>
    """
    reviews = Review.objects.select_related('game', 'author').filter(is_published=True)

    game_slug = request.GET.get('game')
    current_game = None
    if game_slug:
        current_game = get_object_or_404(Game, slug=game_slug)
        reviews = reviews.filter(game=current_game)

    paginator = Paginator(reviews, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'reviews': page_obj.object_list,
        'page_obj': page_obj,
        'current_game': current_game,
    }
    return render(request, 'reviews/review_list.html', context)


def review_detail(request, pk):
    """
    Одна страница обзора.
    """
    review = get_object_or_404(
        Review.objects.select_related('game', 'author'),
        pk=pk,
        is_published=True
    )
    context = {
        'review': review,
    }
    return render(request, 'reviews/review_detail.html', context)


@login_required
def review_create(request, game_slug):
    """
    Создание обзора для игры.
    URL: /reviews/game/<slug>/add/
    """
    game = get_object_or_404(Game, slug=game_slug)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.game = game
            review.author = request.user
            review.save()
            messages.success(request, 'Обзор успешно добавлен.')
            return redirect('review_detail', pk=review.pk)
    else:
        form = ReviewForm()

    context = {
        'game': game,
        'form': form,
    }
    return render(request, 'reviews/review_form.html', context)


@login_required
def review_edit(request, pk):
    review = get_object_or_404(Review, pk=pk)
    if review.author != request.user:
        return HttpResponseForbidden("Вы не можете редактировать этот обзор.")

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Обзор обновлён.')
            return redirect('review_detail', pk=review.pk)
    else:
        form = ReviewForm(instance=review)

    return render(request, 'reviews/review_form.html', {'form': form, 'game': review.game})


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