from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, Q
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from games.utils import paginate_games
from games.models import Game
from .models import Review, ReviewVote, ReviewComment
from .forms import ReviewForm, ReviewImageFormSet, ReviewCommentForm
from urllib.parse import urlparse, parse_qs
from django.contrib.auth.decorators import login_required
from django.db.models import F, Count, Q
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import ReviewCommentForm, ReviewAdminForm
from .models import Review, ReviewVote, ReviewComment
from .utils import can_view_adult, _youtube_to_embed
from datetime import timedelta


def review_list(request):
    qs = Review.objects.select_related("game", "author", "author__profile")

    # показываем только опубликованные
    qs = qs.filter(is_published=True)

    # всего опубликованных (включая 16+)
    total_published = qs.count()

    adult_allowed = can_view_adult(request)
    if not adult_allowed:
        qs = qs.exclude(game__is_adult_only=True)

    # сколько опубликованных доступно пользователю после фильтра 16+
    visible_total = qs.count()

    adult_blocked_only = (not adult_allowed) and (total_published > 0) and (visible_total == 0)
    has_more_adult = (not adult_allowed) and (total_published > visible_total)

    # ✅ поиск по названию игры
    game_search = request.GET.get("game_search", "").strip()
    if game_search:
        q = game_search.casefold()
        qs = qs.filter(
            Q(game__title__icontains=game_search) |
            Q(game__slug__icontains=game_search) |
            Q(title__icontains=game_search) |
            Q(author__username__icontains=game_search) |
            Q(author__profile__nickname__icontains=game_search) |
            Q(game__title__contains=q) |
            Q(author__username__contains=q)
        )

    # (оставим поддержку фильтра из game_detail: ?game=slug)
    game_slug = request.GET.get("game")
    if game_slug:
        qs = qs.filter(game__slug=game_slug)

    sort = request.GET.get("sort", "new")
    if sort == "popular":
        qs = qs.order_by("-views_count", "-created_at")
    elif sort == "rating":
        qs = qs.order_by("-rating", "-created_at")
    else:
        qs = qs.order_by("-created_at")

    reviews, custom_range = paginate_games(request, qs, 6)  # пагинацию не трогаю логически
    params = request.GET.copy()
    params.pop("page", None)
    extra_query = params.urlencode()

    return render(request, "reviews/review_list.html", {
        "reviews": reviews,
        "custom_range": custom_range,
        "extra_query": extra_query,
        "current_sort": sort,
        "game_search": game_search,  # ✅ в шаблон
        "adult_blocked_only": adult_blocked_only,
        "has_more_adult": has_more_adult,

    })


def review_detail(request, pk):
    review = get_object_or_404(
        Review.objects.select_related("game", "author")
        .prefetch_related("images"),
        pk=pk
    )
    adult_allowed = can_view_adult(request)
    if review.game.is_adult_only and not adult_allowed:
        messages.error(request, "Этот обзор доступен только пользователям 16+.")
        return redirect("review_list")

    # если не опубликован — видит только автор/стафф
    if not review.is_published:
        if not request.user.is_authenticated or (request.user != review.author and not request.user.is_staff):
            return HttpResponseForbidden("Обзор на модерации.")

    # просмотры: как games (1 раз за сессию)
    viewed = request.session.get("viewed_reviews", [])
    if review.id not in viewed:
        Review.objects.filter(pk=review.id).update(views_count=F("views_count") + 1)
        viewed.append(review.id)
        request.session["viewed_reviews"] = viewed

    comments = (
        review.comments.filter(is_deleted=False)
        .select_related("user", "user__profile")
        .order_by("-created_at")
    )

    user_vote = None
    if request.user.is_authenticated:
        user_vote = ReviewVote.objects.filter(user=request.user, review=review).first()

    trailer_embed = _youtube_to_embed(review.video_url)

    return render(request, "reviews/review_detail.html", {
        "review": review,
        "comments": comments,
        "comment_form": ReviewCommentForm(),
        "user_vote": user_vote,
        "trailer_embed": trailer_embed,
        'adult_allowed': adult_allowed,
    })


@login_required
def review_create(request, game_slug):
    game = get_object_or_404(Game, slug=game_slug)

    if game.is_adult_only and not can_view_adult(request):
        messages.error(request, "Нельзя создавать обзоры для игр 16+ без подтверждённого возраста.")
        return redirect("review_list")

    if request.method == "POST":
        form = ReviewForm(request.POST, request.FILES)
        formset = ReviewImageFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            review = form.save(commit=False)
            review.game = game
            review.author = request.user

            # модерация: не публикуем сразу
            review.is_published = False

            review.save()
            formset.instance = review
            formset.save()

            messages.success(request, "Обзор отправлен на модерацию.")
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

    if review.author != request.user and not request.user.is_staff:
        return HttpResponseForbidden("Вы не можете редактировать этот обзор.")

    next_url = request.GET.get("next") or request.POST.get("next")

    # ✅ админ редактирует через форму с is_published, обычный юзер — без
    FormClass = ReviewAdminForm if request.user.is_staff else ReviewForm

    if request.method == "POST":
        form = FormClass(request.POST, request.FILES, instance=review)
        formset = ReviewImageFormSet(request.POST, request.FILES, instance=review)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()

            # ✅ только обычный пользователь отправляет повторно на модерацию
            if not request.user.is_staff:
                Review.objects.filter(pk=review.pk).update(is_published=False)

            messages.success(request, "Обзор обновлён.")

            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)

            return redirect("review_detail", pk=review.pk)

    else:
        form = FormClass(instance=review)
        formset = ReviewImageFormSet(instance=review)

    return render(request, "reviews/review_form.html", {
        "game": review.game,
        "form": form,
        "formset": formset,
        "review": review,
        "next": next_url,
    })


@login_required
def review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk)

    if review.author != request.user and not request.user.is_staff:
        return HttpResponseForbidden("Вы не можете снять этот обзор с публикации.")

    next_url = request.GET.get("next") or request.POST.get("next")

    if request.method == "POST":
        review.is_published = False
        review.save(update_fields=["is_published"])
        messages.success(request, "Обзор снят с публикации.")

        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)

        return redirect("review_detail", pk=review.pk)

    return render(request, "reviews/review_confirm_delete.html", {
        "review": review,
        "next": next_url,
    })


@login_required
def review_vote(request, pk):
    review = get_object_or_404(Review, pk=pk)

    if request.method != "POST":
        return redirect("review_detail", pk=pk)

    value = request.POST.get("value")
    if value not in ("1", "-1"):
        return redirect("review_detail", pk=pk)

    vote_value = int(value)

    ReviewVote.objects.update_or_create(
        user=request.user,
        review=review,
        defaults={"value": vote_value},
    )

    # ✅ ключевое: как в games
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"success": True, "value": vote_value})

    messages.success(request, "Ваш голос учтён.")
    return redirect("review_detail", pk=pk)


@login_required
@require_POST
def review_add_comment(request, pk):
    review = get_object_or_404(Review, pk=pk)

    text = request.POST.get("text", "").strip()
    if not text:
        return JsonResponse({"error": "Комментарий пустой"}, status=400)

    # 🔴 ОГРАНИЧЕНИЕ: 1 комментарий в минуту (как в games)
    last_comment = (
        ReviewComment.objects
        .filter(user=request.user, review=review)
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

    comment = ReviewComment.objects.create(
        review=review,
        user=request.user,
        text=text
    )

    html = render_to_string(
        "reviews/partials/review_comment.html",
        {"comment": comment, "user": request.user},
        request=request
    )

    if request.headers.get("X-Requested-With") != "XMLHttpRequest":
        return redirect("review_detail", pk=pk)

    return JsonResponse({"success": True, "html": html}, status=200)


# Удаление комментария к обзору
@require_POST
@login_required(login_url='account_login')
def review_comment_delete(request, pk):
    comment = get_object_or_404(ReviewComment, id=pk)
    review = comment.review

    if not (request.user.is_superuser or request.user == comment.user):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "error": "Нет прав на удаление"}, status=403)
        messages.error(request, "Вы не можете удалить этот комментарий.")
        return redirect("review_detail", pk=review.pk)

    if request.method != "POST":
        return redirect("review_detail", pk=review.pk)

    comment.is_deleted = True
    comment.save(update_fields=["is_deleted"])

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "comment_id": pk})

    messages.success(request, "Комментарий удалён.")
    return redirect("review_detail", pk=review.pk)


# Редактирование комментария к обзору
@login_required(login_url='account_login')
def review_comment_edit(request, pk):
    comment = get_object_or_404(ReviewComment, id=pk, is_deleted=False)
    review = comment.review

    if comment.user != request.user:
        messages.error(request, "Вы можете редактировать только свои комментарии.")
        return redirect("review_detail", pk=review.pk)

    if request.method == "POST":
        form = ReviewCommentForm(request.POST, instance=comment)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.is_edited = True
            comment.save()
            messages.success(request, "Комментарий обновлён.")
            return redirect("review_detail", pk=review.pk)
    else:
        form = ReviewCommentForm(instance=comment)

    context = {
        "review": review,
        "comment": comment,
        "form": form,
    }
    return render(request, "reviews/comment_edit.html", context)
