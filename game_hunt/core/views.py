from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from games.models import Game, GameComment
from games.forms import GameAdminForm, GameImageFormSet, GameAdminPanelForm
from .utils import staff_check
from django.urls import reverse
from reviews.forms import AdminReviewCreateForm, ReviewImageFormSet, ReviewAdminForm
from reviews.models import Review
from django.utils.http import url_has_allowed_host_and_scheme
from walkthroughs.models import Walkthrough
from walkthroughs.forms import AdminWalkthroughCreateForm, WalkthroughImageFormSet, WalkthroughAdminForm
from cheats.models import Cheat
from cheats.forms import CheatAdminPanelCreateForm
from games.models import GameComment
from reviews.models import ReviewComment
from walkthroughs.models import WalkthroughComment
from cheats.models import CheatComment


def homepage(request):
    return render(request, 'home.html')


def about(request):
    return render(request, 'core/about.html')


def contacts(request):
    return render(request, 'core/contacts.html')


def privacy_policy(request):
    return render(request, 'core/privacy_policy.html')


# Главная страница админ-панели
@user_passes_test(staff_check, login_url="account_login")  # CHANGED: login_url
def admin_dashboard(request):
    """
    CHANGED:
    - секции через ?section=games|reviews|walkthroughs|cheats|users
    - поиск через ?q=
    - сортировки: новые сверху
    """
    section = request.GET.get("section", "games")
    q = (request.GET.get("q") or "").strip()

    context = {
        "section": section,
        "q": q,
    }

    if section == "games":
        qs = Game.objects.all().order_by("-created_at", "-id")
        if q:
            qs = qs.filter(title__icontains=q)
        context["games"] = qs

    elif section == "reviews":
        from reviews.models import Review
        qs = (Review.objects
              .select_related("game", "author", "author__profile")
              .order_by('is_published', "-updated_at", "-id"))
        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(game__title__icontains=q) |
                Q(author__username__icontains=q) |
                Q(author__profile__nickname__icontains=q)
            )
        context["reviews"] = qs

    elif section == "walkthroughs":
        from walkthroughs.models import Walkthrough
        qs = (Walkthrough.objects
              .select_related("game", "author", "author__profile")
              .order_by('is_published',"-updated_at", "-id"))
        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(game__title__icontains=q) |
                Q(author__username__icontains=q) |
                Q(author__profile__nickname__icontains=q)
            )
        context["walkthroughs"] = qs

    elif section == "cheats":
        from cheats.models import Cheat
        qs = (Cheat.objects
              .select_related("game", "author", "author__profile")
              .order_by('is_published',"-updated_at", "-id"))
        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(game__title__icontains=q) |
                Q(author__username__icontains=q) |
                Q(author__profile__nickname__icontains=q)
            )
        context["cheats"] = qs

    elif section == "users":
        qs = User.objects.select_related("profile").order_by("username")
        if q:
            qs = qs.filter(
                Q(username__icontains=q) |
                Q(profile__nickname__icontains=q)
            )
        context["users"] = qs

    return render(request, "core/admin_dashboard.html", context)


@user_passes_test(staff_check, login_url="account_login")
def admin_game_create(request):
    template_name = "core/game_form.html"
    next_url = request.POST.get("next") or request.GET.get("next")

    if request.method == "POST":
        form = GameAdminPanelForm(request.POST, request.FILES)

        if form.is_valid():
            with transaction.atomic():
                game = form.save()  # slug генерится в форме
                formset = GameImageFormSet(request.POST, request.FILES, instance=game)

                if formset.is_valid():
                    formset.save()
                    messages.success(request, f'Игра "{game.title}" добавлена.')
                    return redirect(next_url or (reverse("admin_dashboard") + "?section=games"))

                # если картинки невалидны — откатываем создание игры
                transaction.set_rollback(True)
        else:
            game = None

        # если форма/формсет невалидны — показать ошибки
        formset = GameImageFormSet(request.POST, request.FILES)

    else:
        form = GameAdminPanelForm()
        formset = GameImageFormSet()
        game = None

    return render(request, template_name, {
        "form": form,
        "formset": formset,
        "next": next_url,
        "game": game,
    })


@user_passes_test(staff_check, login_url="account_login")
def admin_game_edit(request, pk):
    template_name = "core/game_form.html"
    next_url = request.POST.get("next") or request.GET.get("next")

    game = get_object_or_404(Game, pk=pk)

    if request.method == "POST":
        form = GameAdminPanelForm(request.POST, request.FILES, instance=game)
        formset = GameImageFormSet(request.POST, request.FILES, instance=game)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
                messages.success(request, f'Игра "{game.title}" обновлена.')
            return redirect(next_url or (reverse("admin_dashboard") + "?section=games"))

        # если невалидно — просто рендерим с ошибками

    else:
        form = GameAdminPanelForm(instance=game)
        formset = GameImageFormSet(instance=game)

    return render(request, template_name, {
        "form": form,
        "formset": formset,
        "next": next_url,
        "game": game,
    })


# Удаление игры (мягко, без удаления из БД)
@user_passes_test(staff_check, login_url="account_login")  # CHANGED
def admin_game_delete(request, pk):
    game = get_object_or_404(Game, pk=pk)

    if request.method == 'POST':
        # CHANGED: вместо delete() делаем снятие с публикации
        if hasattr(game, "is_published"):
            game.is_published = False
            game.save(update_fields=["is_published"])
            messages.success(request, f'Игра "{game.title}" снята с публикации.')
        else:
            # если поля нет — хотя бы не молча, но лучше потом добавим
            game.delete()
            messages.success(request, f'Игра "{game.title}" удалена.')

        return redirect("/admin-panel/?section=games")

    return render(request, 'core/admin_game_confirm_delete.html', {
        'game': game,
    })


@user_passes_test(staff_check, login_url="account_login")
def admin_user_comments(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    kind = request.GET.get("kind", "games")  # games|reviews|walkthroughs|cheats

    sources = {
        "games": (
            GameComment.objects
            .filter(user=target_user, is_deleted=False)
            .select_related("game")
            .order_by("-updated_at")
        ),
        "reviews": (
            ReviewComment.objects
            .filter(user=target_user, is_deleted=False)
            .select_related("review", "review__game")
            .order_by("-updated_at")
        ),
        "walkthroughs": (
            WalkthroughComment.objects
            .filter(user=target_user, is_deleted=False)
            .select_related("walkthrough", "walkthrough__game")
            .order_by("-updated_at")
        ),
        "cheats": (
            CheatComment.objects
            .filter(user=target_user, is_deleted=False)
            .select_related("cheat", "cheat__game")
            .order_by("-updated_at")
        ),
    }

    if kind not in sources:
        kind = "games"

    kinds = [
        ("games", "К играм"),
        ("reviews", "К обзорам"),
        ("walkthroughs", "К прохождениям"),
        ("cheats", "К читам"),
    ]

    return render(request, "core/admin_user_comments.html", {
        "target_user": target_user,
        "kind": kind,
        "kinds": kinds,
        "comments": sources[kind],
    })


# Бан/разбан пользователя (fallback с редиректом)
@user_passes_test(staff_check, login_url="account_login")  # CHANGED
def admin_toggle_ban(request, user_id):
    user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        if user.is_active:
            messages.success(request, f'Пользователь {user.username} разблокирован.')
        else:
            messages.warning(request, f'Пользователь {user.username} заблокирован.')

    # CHANGED: обратно в users секцию
    return redirect("/admin-panel/?section=users")


# CHANGED: AJAX бан/разбан без перезагрузки
@require_POST
@user_passes_test(staff_check, login_url="account_login")
def admin_toggle_ban_ajax(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])
    return JsonResponse({
        "ok": True,
        "user_id": user.id,
        "is_active": user.is_active,
    })


@user_passes_test(staff_check, login_url="account_login")
def admin_review_create(request):

    template_name = "reviews/review_form.html"
    next_url = request.POST.get("next") or request.GET.get("next")

    if request.method == "POST":
        form = AdminReviewCreateForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                review = form.save(commit=False)
                review.author = request.user
                review.is_published = True
                review.save()

                formset = ReviewImageFormSet(request.POST, request.FILES, instance=review)
                if formset.is_valid():
                    formset.save()
                    messages.success(request, f'Обзор "{review.title}" добавлен.')
                    return redirect(next_url or (reverse("admin_dashboard") + "?section=reviews"))

                transaction.set_rollback(True)
        formset = ReviewImageFormSet(request.POST, request.FILES)
    else:
        form = AdminReviewCreateForm()
        formset = ReviewImageFormSet()

    return render(request, template_name, {
        "form": form,
        "formset": formset,
        "next": next_url,
        "is_create": True,
    })


@user_passes_test(staff_check, login_url="account_login")
def admin_review_edit(request, pk):
    review = get_object_or_404(Review, pk=pk)
    next_url = request.GET.get("next") or request.POST.get("next")

    if request.method == "POST":
        form = ReviewAdminForm(request.POST, request.FILES, instance=review)
        formset = ReviewImageFormSet(request.POST, request.FILES, instance=review)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Обзор обновлён (модерация).")

            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)

            return redirect("review_detail", pk=review.pk)
    else:
        form = ReviewAdminForm(instance=review)
        formset = ReviewImageFormSet(instance=review)

    return render(request, "reviews/review_form.html", {
        "game": review.game,
        "form": form,
        "formset": formset,
        "review": review,
        "next": next_url,
    })


@user_passes_test(staff_check, login_url="account_login")
def admin_walkthrough_create(request):
    next_url = request.GET.get("next") or request.POST.get("next")

    if request.method == "POST":
        form = AdminWalkthroughCreateForm(request.POST, request.FILES)
        formset = WalkthroughImageFormSet(request.POST, request.FILES)

        if form.is_valid() and formset.is_valid():
            walkthrough = form.save(commit=False)
            walkthrough.author = request.user
            walkthrough.is_published = True
            walkthrough.save()

            formset.instance = walkthrough
            formset.save()

            messages.success(request, "Прохождение добавлено.")
            return redirect(next_url or (reverse("admin_dashboard") + "?section=walkthroughs"))
    else:
        form = AdminWalkthroughCreateForm()
        formset = WalkthroughImageFormSet()

    return render(request, "walkthroughs/walkthrough_form.html", {
        "form": form,
        "formset": formset,
        "walkthrough": None,
        "next": next_url,
    })

@user_passes_test(staff_check, login_url="account_login")
def admin_walkthrough_edit(request, slug):
    walkthrough = get_object_or_404(Walkthrough, slug=slug)
    next_url = request.GET.get("next") or request.POST.get("next")

    if request.method == "POST":
        form = WalkthroughAdminForm(request.POST, request.FILES, instance=walkthrough)
        formset = WalkthroughImageFormSet(request.POST, request.FILES, instance=walkthrough)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Прохождение обновлено (модерация).")

            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)

            return redirect("walkthrough_detail", slug=walkthrough.slug)
    else:
        form = WalkthroughAdminForm(instance=walkthrough)
        formset = WalkthroughImageFormSet(instance=walkthrough)

    return render(request, "walkthroughs/walkthrough_form.html", {
        "game": walkthrough.game,
        "form": form,
        "formset": formset,
        "walkthrough": walkthrough,
        "next": next_url,
    })


@user_passes_test(staff_check, login_url="account_login")
def admin_cheat_create(request):
    template_name = "cheats/cheat_form.html"  # если у тебя путь другой — поставь свой
    next_url = request.POST.get("next") or request.GET.get("next")

    if request.method == "POST":
        form = CheatAdminPanelCreateForm(request.POST, request.FILES)

        if form.is_valid():
            cheat = form.save(commit=False)
            cheat.author = request.user
            cheat.is_published = True
            cheat.save()
            form.save_m2m()

            messages.success(request, f'Чит "{cheat.title}" добавлен и опубликован.')
            return redirect(next_url or (reverse("admin_dashboard") + "?section=cheats"))
    else:
        form = CheatAdminPanelCreateForm()

    return render(request, template_name, {
        "form": form,
        "cheat": None,
        "game": None,   # заголовок в шаблоне и так корректно отработает
        "next": next_url,
    })