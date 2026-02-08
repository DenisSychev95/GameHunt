from datetime import timedelta
import os
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import F, Q
from django.http import JsonResponse, Http404, FileResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.conf import settings
from games.utils import paginate_games
from .models import Cheat, CheatVote, CheatComment
from .forms import CheatFormAdminCreate, CheatFormAdminEdit, CheatCommentForm, CheatFormStaffCreateForGame
from games.models import Game


def staff_check(u):
    return u.is_authenticated and (u.is_staff or u.is_superuser)


def cheat_list(request):
    qs = (
        Cheat.objects
        .select_related("game", "author", "author__profile")
        .filter(is_published=True)
    )

    game_search = request.GET.get("game_search", "").strip()
    if game_search:
        qs = qs.filter(
            Q(game__title__icontains=game_search) |
            Q(game__slug__icontains=game_search) |
            Q(title__icontains=game_search) |  # название чита
            Q(author__username__icontains=game_search) |
            Q(author__profile__nickname__icontains=game_search)
        )

    sort = request.GET.get("sort", "new")
    if sort == "popular":
        qs = qs.order_by("-downloads_count", "-views_count", )
    else:
        qs = qs.order_by("-created_at", )

    cheats, custom_range = paginate_games(request, qs, 3)

    params = request.GET.copy()
    params.pop("page", None)
    extra_query = params.urlencode()

    return render(request, "cheats/cheat_list.html", {
        "cheats": cheats,
        "custom_range": custom_range,
        "extra_query": extra_query,
        "current_sort": sort,
        "game_search": game_search,
    })


def cheat_detail(request, slug):
    cheat = get_object_or_404(
        Cheat.objects.select_related("game", "author", "author__profile"),
        slug=slug,
    )

    # если снят с публикации — показываем только staff/superuser
    if not cheat.is_published:
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            raise Http404

    # +1 просмотр за сессию
    viewed = request.session.get("viewed_cheats", [])
    if cheat.id not in viewed:
        Cheat.objects.filter(pk=cheat.id).update(views_count=F("views_count") + 1)
        viewed.append(cheat.id)
        request.session["viewed_cheats"] = viewed

    comments = (
        cheat.comments.filter(is_deleted=False)
        .select_related("user", "user__profile")
        .order_by("-created_at")
    )
    cheat_filename = os.path.basename(cheat.cheat_file.name) if cheat.cheat_file else ""

    user_vote = None
    if request.user.is_authenticated:
        user_vote = CheatVote.objects.filter(user=request.user, cheat=cheat).first()

    return render(request, "cheats/cheat_detail.html", {
        "cheat": cheat,
        "comments": comments,
        "comment_form": CheatCommentForm(),
        "user_vote": user_vote,
        "cheat_filename": cheat_filename,
    })


@user_passes_test(staff_check, login_url="account_login")
def cheat_create_for_game(request, game_slug):
    game = get_object_or_404(Game, slug=game_slug)

    if request.method == "POST":
        form = CheatFormStaffCreateForGame(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.game = game
            obj.author = request.user
            obj.is_published = True  # раз админ — сразу публикуем
            obj.save()
            messages.success(request, "Чит создан.")
            return redirect("game_detail", slug=game.slug)
    else:
        form = CheatFormStaffCreateForGame()

    return render(request, "cheats/cheat_form.html", {
        "form": form,
        "cheat": None,
        "game": game,
    })


@user_passes_test(staff_check, login_url="account_login")
def cheat_create(request):
    if request.method == "POST":
        form = CheatFormAdminCreate(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.author = request.user
            obj.save()
            messages.success(request, "Чит создан.")
            return redirect("cheat_detail", slug=obj.slug)
    else:
        form = CheatFormAdminCreate()

    return render(request, "cheats/cheat_form.html", {"form": form, "cheat": None, "game": None})


@user_passes_test(staff_check, login_url="account_login")
def cheat_edit(request, slug):
    cheat = get_object_or_404(Cheat, slug=slug)

    # ✅ редактировать может только админ, который является автором чита
    if not (request.user.is_staff and request.user == cheat.author):
        return HttpResponseForbidden("Вы не можете редактировать этот чит.")

    if request.method == "POST":
        form = CheatFormAdminEdit(request.POST, request.FILES, instance=cheat)
        if form.is_valid():
            form.save()
            messages.success(request, "Чит обновлён.")
            return redirect("cheat_detail", slug=cheat.slug)
    else:
        form = CheatFormAdminEdit(instance=cheat)

    return render(request, "cheats/cheat_form.html", {"form": form, "cheat": cheat})


@user_passes_test(staff_check, login_url="account_login")
def cheat_delete(request, slug):
    cheat = get_object_or_404(Cheat, slug=slug)

    # ✅ снять с публикации может любой админ/стафф
    if not request.user.is_staff:
        return HttpResponseForbidden("Вы не можете снять этот чит с публикации.")

    if request.method == "POST":
        cheat.is_published = False
        cheat.save(update_fields=["is_published"])
        messages.success(request, "Чит снят с публикации.")
        return redirect("cheat_list")

    return render(request, "cheats/cheat_confirm_delete.html", {"cheat": cheat})



@login_required
def cheat_vote(request, slug):
    cheat = get_object_or_404(Cheat, slug=slug)

    if request.method != "POST":
        return redirect("cheat_detail", slug=slug)

    value = request.POST.get("value")
    if value not in ("1", "-1"):
        return redirect("cheat_detail", slug=slug)

    vote_value = int(value)

    CheatVote.objects.update_or_create(
        user=request.user,
        cheat=cheat,
        defaults={"value": vote_value},
    )

    # пересчитать liked_percent
    cheat.recalc_liked_percent()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"success": True, "value": vote_value})

    messages.success(request, "Ваш голос учтён.")
    return redirect("cheat_detail", slug=slug)


@login_required(login_url="account_login")
@require_POST
def cheat_add_comment(request, slug):
    cheat = get_object_or_404(Cheat, slug=slug)

    text = request.POST.get("text", "").strip()
    if not text:
        return JsonResponse({"error": "Комментарий пустой"}, status=400)

    # 1 раз в минуту (как walkthroughs)
    last_comment = (
        CheatComment.objects
        .filter(user=request.user, cheat=cheat)
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

    comment = CheatComment.objects.create(
        cheat=cheat,
        user=request.user,
        text=text,
    )

    html = render_to_string(
        "cheats/partials/cheat_comment.html",
        {"comment": comment, "user": request.user},
        request=request
    )
    return JsonResponse({"success": True, "html": html}, status=200)


@login_required(login_url="account_login")
@require_POST
def cheat_comment_delete(request, pk):
    comment = get_object_or_404(CheatComment, pk=pk)
    cheat = comment.cheat

    # ✅ удалить (скрыть) может автор коммента или любой staff/superuser
    if not (request.user.is_staff or request.user.is_superuser or request.user == comment.user):
        return JsonResponse({"ok": False, "error": "Нет прав на удаление"}, status=403)

    comment.is_deleted = True
    comment.save(update_fields=["is_deleted"])
    return JsonResponse({"ok": True, "id": comment.id})


@login_required(login_url="account_login")
def cheat_comment_edit(request, pk):
    comment = get_object_or_404(CheatComment, pk=pk, is_deleted=False)
    cheat = comment.cheat

    # ✅ редактировать может только автор
    if comment.user != request.user:
        messages.error(request, "Можно редактировать только свои комментарии.")
        return redirect("cheat_detail", slug=cheat.slug)

    if request.method == "POST":
        form = CheatCommentForm(request.POST, instance=comment)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.is_edited = True
            obj.save(update_fields=["text", "is_edited", "updated_at"])
            messages.success(request, "Комментарий обновлён.")
            return redirect("cheat_detail", slug=cheat.slug)
    else:
        form = CheatCommentForm(instance=comment)

    return render(request, "cheats/comment_edit.html", {
        "form": form,
        "comment": comment,
        "cheat": cheat,
    })


def cheat_download(request, slug):
    # скачивать могут только авторизованные
    if not request.user.is_authenticated:
        return redirect(f"{settings.LOGIN_URL}?next={request.path}")

    cheat = get_object_or_404(Cheat, slug=slug)

    # если снят с публикации — можно скачать только staff/автор (по желанию)
    if not cheat.is_published and not (request.user.is_staff or request.user == cheat.author):
        raise Http404

    if not cheat.cheat_file:
        raise Http404("Файл не найден")

    downloaded = request.session.get("downloaded_cheats", [])
    if cheat.id not in downloaded:
        Cheat.objects.filter(pk=cheat.id).update(downloads_count=F("downloads_count") + 1)
        downloaded.append(cheat.id)
        request.session["downloaded_cheats"] = downloaded

    filename = os.path.basename(cheat.cheat_file.name)
    return FileResponse(cheat.cheat_file.open("rb"), as_attachment=True, filename=filename)