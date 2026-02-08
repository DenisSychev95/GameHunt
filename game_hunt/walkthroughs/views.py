from games.utils import paginate_games
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F
from django.http import JsonResponse, HttpResponseForbidden
from django.template.loader import render_to_string
from games.models import Game
from reviews.utils import can_view_adult, _youtube_to_embed
from .models import Walkthrough, WalkthroughVote, WalkthroughComment
from .forms import WalkthroughFormUser, WalkthroughImageFormSet, WalkthroughCommentForm, WalkthroughFormStaff
from django.views.decorators.http import require_POST
from datetime import timedelta
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme


def walkthrough_list(request):
    qs = (
        Walkthrough.objects
        .select_related("game", "author", "author__profile")
        .filter(is_published=True)
    )

    # ---- поиск: по названию игры + по нику автора ----
    search_query = request.GET.get("search", "").strip()
    if search_query:
        qs = qs.filter(
            Q(title__icontains=search_query) |
            Q(game__title__icontains=search_query) |
            Q(author__username__icontains=search_query) |
            Q(author__profile__nickname__icontains=search_query)
        )

    # ---- возрастной фильтр (16+) ----
    total_found = qs.count()  # всего найдено (включая 16+)
    adult_allowed = can_view_adult(request)

    if not adult_allowed:
        qs = qs.exclude(game__is_adult_only=True)

    visible_total = qs.count()  # сколько реально можно показать

    adult_blocked_only = (not adult_allowed) and (total_found > 0) and (visible_total == 0)
    has_more_adult = (not adult_allowed) and (total_found > visible_total)

    # ---- сортировка ----
    sort = request.GET.get("sort", "new")
    if sort == "popular":
        qs = qs.order_by("-views_count", "-updated_at", "-id")
    else:
        qs = qs.order_by("-updated_at", "-id")

    # ---- пагинация: 3 карточки ----
    walkthroughs, custom_range = paginate_games(request, qs, 3)

    params = request.GET.copy()
    params.pop("page", None)
    extra_query = params.urlencode()

    return render(request, "walkthroughs/walkthrough_list.html", {
        "walkthroughs": walkthroughs,
        "custom_range": custom_range,
        "extra_query": extra_query,
        "current_sort": sort,
        "search_query": search_query,
        "adult_blocked_only": adult_blocked_only,
        "has_more_adult": has_more_adult,
    })


def walkthrough_detail(request, slug):
    walkthrough = get_object_or_404(
        Walkthrough.objects.select_related("game", "author", "author__profile")
        .prefetch_related("images"),
        slug=slug,
    )

    adult_allowed = can_view_adult(request)
    if walkthrough.game.is_adult_only and not adult_allowed:
        messages.error(request, "Это прохождение доступно только пользователям 16+.")
        return redirect("walkthrough_list")

    # если не опубликован — видит только автор/стафф
    if not walkthrough.is_published:
        if not request.user.is_authenticated or (request.user != walkthrough.author and not request.user.is_staff):
            return HttpResponseForbidden("Прохождение на модерации.")

    # views_count 1 раз за сессию
    viewed = request.session.get("viewed_walkthroughs", [])
    if walkthrough.id not in viewed:
        Walkthrough.objects.filter(pk=walkthrough.id).update(views_count=F("views_count") + 1)
        viewed.append(walkthrough.id)
        request.session["viewed_walkthroughs"] = viewed

    comments = (
        walkthrough.comments.filter(is_deleted=False)
        .select_related("user", "user__profile")
        .order_by("-created_at")
    )

    user_vote = None
    if request.user.is_authenticated:
        user_vote = WalkthroughVote.objects.filter(user=request.user, walkthrough=walkthrough).first()

    video_embed = _youtube_to_embed(walkthrough.video_url)

    return render(request, "walkthroughs/walkthrough_detail.html", {
        "walkthrough": walkthrough,
        "comments": comments,
        "comment_form": WalkthroughCommentForm(),
        "user_vote": user_vote,
        "video_embed": video_embed,
        "adult_allowed": adult_allowed,
    })


@login_required
def walkthrough_create(request, game_slug):
    game = get_object_or_404(Game, slug=game_slug)

    # 16+ ограничения такие же как в обзорах
    if game.is_adult_only and not can_view_adult(request):
        messages.error(request, "Это прохождение доступно только пользователям 16+.")
        return redirect("walkthrough_list")

    if request.method == "POST":
        form = WalkthroughFormUser(request.POST, request.FILES)
        formset = WalkthroughImageFormSet(request.POST, request.FILES)

        if form.is_valid() and formset.is_valid():
            wt = form.save(commit=False)
            wt.game = game
            wt.author = request.user
            wt.is_published = False  # пользователь -> на модерацию
            wt.save()

            formset.instance = wt
            formset.save()

            messages.success(request, "Прохождение отправлено на модерацию.")
            return redirect("walkthrough_detail", slug=wt.slug)
    else:
        form = WalkthroughFormUser()
        formset = WalkthroughImageFormSet()

    return render(request, "walkthroughs/walkthrough_form.html", {
        "form": form,
        "formset": formset,
        "game": game,
        "walkthrough": None,
    })


@login_required(login_url="account_login")
def walkthrough_edit(request, slug):
    wt = get_object_or_404(Walkthrough, slug=slug)

    # 16+
    if wt.game.is_adult_only and not can_view_adult(request):
        messages.error(request, "Это прохождение доступно только пользователям 16+.")
        return redirect("walkthrough_list")

    if wt.author != request.user and not request.user.is_staff:
        return HttpResponseForbidden("Вы не можете редактировать это прохождение.")

    next_url = request.GET.get("next") or request.POST.get("next")

    # ✅ админ/стафф — форма с is_published, обычный — без
    FormClass = WalkthroughFormStaff if request.user.is_staff else WalkthroughFormUser

    if request.method == "POST":
        form = FormClass(request.POST, request.FILES, instance=wt)
        formset = WalkthroughImageFormSet(request.POST, request.FILES, instance=wt)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()

            # после правок обычного пользователя снова на модерацию
            if not request.user.is_staff:
                Walkthrough.objects.filter(pk=wt.pk).update(is_published=False)

            messages.success(request, "Прохождение обновлено.")

            # ✅ если пришли из профиля — вернём в профиль
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)

            return redirect("walkthrough_detail", slug=wt.slug)

    else:
        form = FormClass(instance=wt)
        formset = WalkthroughImageFormSet(instance=wt)

    return render(request, "walkthroughs/walkthrough_form.html", {
        "game": wt.game,
        "form": form,
        "formset": formset,
        "walkthrough": wt,
        "next": next_url,  # ✅ нужно для hidden input в шаблоне
    })


@login_required
def walkthrough_delete(request, slug):
    wt = get_object_or_404(Walkthrough, slug=slug)

    # админ может снять любой, пользователь — только своё
    if not (request.user.is_staff or request.user == wt.author):
        return HttpResponseForbidden("Вы не можете снять это прохождение с публикации.")

    next_url = request.GET.get("next") or request.POST.get("next")

    if request.method == "POST":
        wt.is_published = False
        wt.save(update_fields=["is_published"])
        messages.success(request, "Прохождение снято с публикации.")

        # ✅ если пришли из профиля — вернём в профиль
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)

        # fallback: если снимали с карточки прохождения — вернём на неё
        return redirect("walkthrough_detail", slug=wt.slug)

    return render(request, "walkthroughs/walkthrough_confirm_delete.html", {
        "walkthrough": wt,
        "next": next_url,
    })


@login_required
def walkthrough_vote(request, slug):
    wt = get_object_or_404(Walkthrough, slug=slug)

    if request.method != "POST":
        return redirect("walkthrough_detail", slug=slug)

    value = request.POST.get("value")
    if value not in ("1", "-1"):
        return redirect("walkthrough_detail", slug=slug)

    vote_value = int(value)

    WalkthroughVote.objects.update_or_create(
        user=request.user,
        walkthrough=wt,
        defaults={"value": vote_value},
    )

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"success": True, "value": vote_value})

    messages.success(request, "Ваш голос учтён.")
    return redirect("walkthrough_detail", slug=slug)


@login_required(login_url="account_login")
@require_POST
def walkthrough_add_comment(request, slug):
    wt = get_object_or_404(Walkthrough, slug=slug)

    text = request.POST.get("text", "").strip()
    if not text:
        if request.headers.get("X-Requested-With") != "XMLHttpRequest":
            return redirect("walkthrough_detail", slug=slug)
        return JsonResponse({"error": "Комментарий пустой"}, status=400)

    # 🔴 ограничение: 1 комментарий в минуту (как в games)
    last_comment = (
        WalkthroughComment.objects
        .filter(user=request.user, walkthrough=wt)
        .order_by("-created_at")
        .first()
    )
    if last_comment:
        delta = timezone.now() - last_comment.created_at
        if delta < timedelta(minutes=1):
            seconds_left = 60 - int(delta.total_seconds())
            msg = f"Можно комментировать раз в минуту. Подождите {seconds_left} сек."
            if request.headers.get("X-Requested-With") != "XMLHttpRequest":
                return redirect("walkthrough_detail", slug=slug)
            return JsonResponse({"error": msg}, status=429)

    comment = WalkthroughComment.objects.create(
        walkthrough=wt,
        user=request.user,
        text=text
    )

    html = render_to_string(
        "walkthroughs/partials/walkthrough_comment.html",
        {"comment": comment, "user": request.user},
        request=request
    )

    if request.headers.get("X-Requested-With") != "XMLHttpRequest":
        return redirect("walkthrough_detail", slug=slug)

    return JsonResponse({"success": True, "html": html}, status=200)


@login_required
@require_POST
def walkthrough_comment_delete(request, pk):
    comment = get_object_or_404(WalkthroughComment, id=pk)
    wt = comment.walkthrough

    # админ может удалить любой, пользователь только свой
    if not (request.user.is_superuser or request.user.is_staff or request.user == comment.user):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "error": "Нет прав на удаление"}, status=403)
        messages.error(request, "Вы не можете удалить этот комментарий.")
        return redirect("walkthrough_detail", slug=wt.slug)

    comment.is_deleted = True
    comment.save(update_fields=["is_deleted"])

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "id": comment.id})

    messages.success(request, "Комментарий удалён.")
    return redirect("walkthrough_detail", slug=wt.slug)


@login_required
def walkthrough_comment_edit(request, pk):
    comment = get_object_or_404(WalkthroughComment, id=pk, is_deleted=False)
    wt = comment.walkthrough

    # редактировать только свои (как в обзорах)
    if comment.user != request.user:
        messages.error(request, "Вы можете редактировать только свои комментарии.")
        return redirect("walkthrough_detail", slug=wt.slug)

    if request.method == "POST":
        form = WalkthroughCommentForm(request.POST, instance=comment)
        if form.is_valid():
            c = form.save(commit=False)
            c.is_edited = True
            c.save(update_fields=["text", "is_edited", "updated_at"])
            messages.success(request, "Комментарий обновлён.")
            return redirect("walkthrough_detail", slug=wt.slug)
    else:
        form = WalkthroughCommentForm(instance=comment)

    return render(request, "walkthroughs/comment_edit.html", {"form": form, "comment": comment, "walkthrough": wt})