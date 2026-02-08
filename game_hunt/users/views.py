from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import ProfileEditForm, ProfileImageEditForm
from django.contrib import messages
from .models import Profile, AdminMessages, UserMessages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .forms import GuestToAdminForm, AuthUserToAdminForm, AdminSendUserMessageForm
from django.db import transaction
from .telegram_notify import tg_send_admin
from .utils import build_profile_content


@login_required(login_url='account_login')
def profile(request):
    account_profile = (
        Profile.objects
        .select_related('user')
        .prefetch_related('favorite_genres')
        .get(user=request.user)
    )
    context = {'profile': account_profile}
    context.update(build_profile_content(request, account_profile.user, is_owner=True))
    return render(request, 'accounts/profile.html', context)


def profile_view(request, pk):
    pr = get_object_or_404(Profile, id=pk)
    if not request.user.is_authenticated:
        messages.error(request, "Просматривать профили могут только зарегистрированные пользователи.")
        # Пытаемся вернуть пользователя на предыдущую станицу, страницу с игрой(на ту же страницу, где были)
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        # На случай если объект referer отсутствует, перенаправляем на страницу с играми(прямой ввод в адресную строку)
        return redirect('game_list')
    context = {
        'profile': pr
    }
    is_owner = (request.user == pr.user)
    context.update(build_profile_content(request, pr.user, is_owner=is_owner))

    return render(request, 'accounts/profile.html', context)


@login_required(login_url='account_login')
def profile_edit(request):
    profile = request.user.profile  # профайл уже создаётся сигналом post_save

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлён.')
            return redirect('profile') # после сохранения перенаправляем в профиль
    else:
        form = ProfileEditForm(instance=profile)

    context = {
        'form': form,
    }
    return render(request, 'accounts/profile_edit.html', context)


@login_required(login_url="account_login")
def profile_image_edit(request):
    profile = request.user.profile

    if request.method == "POST":
        old_image = profile.profile_image
        form = ProfileImageEditForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            form.save()

            # удалить старый файл, если заменили
            if "profile_image" in form.changed_data:
                if old_image and old_image.name and old_image.name != "default.png":
                    old_image.delete(save=False)

            messages.success(request, "Фото профиля обновлено.")
            return redirect("profile")
    else:
        form = ProfileImageEditForm(instance=profile)

    return render(request, "accounts/profile_image_edit.html", {"form": form})


def _is_admin(u):
    return u.is_authenticated and (u.is_staff or u.is_superuser)


@user_passes_test(_is_admin, login_url="account_login")
def admin_messages_inbox(request):
    mode = request.GET.get("mode", "all")
    if mode not in ("all", "admin", "user"):
        mode = "admin"

    tab = request.GET.get("tab", "all")
    if tab not in ("unread", "read", "all"):
        tab = "unread"

    # tab фильтр
    def apply_read_filter(qs):
        if tab == "unread":
            return qs.filter(is_read=False)
        if tab == "read":
            return qs.filter(is_read=True)
        return qs  # all

    # ✅ ALL: оба потока, но с учетом tab
    if mode == "all":
        admin_items = apply_read_filter(AdminMessages.objects.filter(is_published=True).order_by("is_read", '-created_at'))
        user_items = apply_read_filter(UserMessages.objects.filter(user=request.user, is_published=True).order_by("is_read", '-created_at'))

        return render(request, "users/admin_messages_inbox.html", {
            "mode": "all",
            "tab": tab,
            "admin_items": admin_items,
            "user_items": user_items,
        })

    # один поток
    if mode == "user":
        items = apply_read_filter(UserMessages.objects.filter(user=request.user, is_published=True).order_by("is_read", '-created_at'))
    else:
        items = apply_read_filter(AdminMessages.objects.filter(is_published=True).order_by("is_read", '-created_at'))

    return render(request, "users/admin_messages_inbox.html", {
        "mode": mode,
        "tab": tab,
        "items": items,
    })


@user_passes_test(_is_admin, login_url="account_login")
def admin_message_detail(request, pk):
    m = get_object_or_404(AdminMessages, pk=pk)

    # От кого
    if m.user_id:
        sender = "Администрация сайта" if (m.user.is_staff or m.user.is_superuser) else (
            getattr(getattr(m.user, "profile", None), "nickname", None) or m.user.username
        )
        email = ""  # для авторизованных в админских сообщениях почту не показываем
    else:
        sender = m.guest_name or "Гость"
        email = m.guest_email or ""

    # Тема (красивое отображение)
    if m.topic == "other" and (m.topic_custom or "").strip():
        topic_display = m.topic_custom.strip()
    else:
        # если у topic есть choices — будет человекочитаемо, иначе вернём значение
        try:
            topic_display = m.get_topic_display()
        except Exception:
            topic_display = m.topic

    return JsonResponse({
        "id": m.pk,
        "created_at": m.created_at.strftime("%d.%m.%Y %H:%M"),
        "from": sender,
        "email": email,
        "topic": topic_display,
        "short": (m.topic_custom or "").strip(),   # кратко
        "body": m.message,
        "link": "",
        "image_url": m.image.url if m.image else None,
    })


@require_POST
@user_passes_test(_is_admin, login_url="account_login")
def admin_message_mark_read(request, pk):
    m = get_object_or_404(AdminMessages, pk=pk)
    if not m.is_read:
        m.is_read = True
        if m.status == "created":
            m.status = "in_review"
            m.save(update_fields=["is_read", "status"])
        else:
            m.save(update_fields=["is_read"])
    return JsonResponse({"ok": True})


@require_POST
@user_passes_test(_is_admin, login_url="account_login")
def admin_message_unpublish(request, pk):
    m = get_object_or_404(AdminMessages, pk=pk)

    if not m.is_read:
        return JsonResponse({"ok": False, "error": "not_read"}, status=400)

    if m.status != "processed":
        return JsonResponse({"ok": False, "error": "not_processed"}, status=400)

    m.is_published = False
    m.save(update_fields=["is_published"])
    return JsonResponse({"ok": True})


# notifications list
@login_required(login_url="account_login")
def notifications(request):
    tab = request.GET.get("tab", "all")
    qs = UserMessages.objects.filter(user=request.user, is_published=True).order_by("-created_at")

    if tab == "unread":
        qs = qs.filter(is_read=False)
    elif tab == "read":
        qs = qs.filter(is_read=True)
    elif tab == "all":
        pass
    else:
        tab = "unread"
        qs = qs.filter(is_read=False)

    return render(request, "users/notifications.html", {
        "items": qs,
        "tab": tab,
    })


@login_required(login_url="account_login")
def notification_detail(request, pk):
    n = get_object_or_404(UserMessages, pk=pk, user=request.user)

    return JsonResponse({
        "id": n.pk,
        "created_at": n.created_at.strftime("%d.%m.%Y %H:%M"),
        "from": n.sender,
        "email": "",  # для пользовательских уведомлений почту не показываем
        "topic": n.get_topic_display(),
        "short": (n.title or "").strip(),     # "Кратко"
        "body": n.text,                       # текст уведомления
        "link": (n.link or "").strip(),       # ссылка (если есть)
        "image_url": n.image.url if n.image else None,
    })


@require_POST
@login_required(login_url="account_login")
def notification_mark_read(request, pk):
    n = get_object_or_404(UserMessages, pk=pk, user=request.user)
    if not n.is_read:
        n.is_read = True
        n.save(update_fields=["is_read"])
    return JsonResponse({"ok": True})


@require_POST
@login_required(login_url="account_login")
def notification_unpublish(request, pk):
    n = get_object_or_404(UserMessages, pk=pk, user=request.user)
    if not n.is_read:
        return JsonResponse({"ok": False, "error": "not_read"}, status=400)

    n.is_published = False
    n.save(update_fields=["is_published"])
    return JsonResponse({"ok": True})


def contact_admin(request):
    if request.user.is_authenticated:
        form_class = AuthUserToAdminForm
    else:
        form_class = GuestToAdminForm

    if request.method == "POST":
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)

            if request.user.is_authenticated:
                obj.user = request.user

                # имя берём из profile.first_name, иначе "Имя не указано"
                first_name = (request.user.profile.first_name or "").strip() if hasattr(request.user, "profile") else ""
                obj.guest_name = first_name or "Имя не указано"

                # email — из User
                obj.guest_email = request.user.email or ""

            # для гостя: user остаётся None, guest_name/email уже из формы
            obj.save()

            def _notify():
                if obj.user_id:
                    who = obj.user.profile.nickname or obj.user.username
                else:
                    who = obj.guest_name or "Гость"
                    if obj.guest_email:
                        who = f"{who} ({obj.guest_email})"

                if obj.topic == "other" and (obj.topic_custom or "").strip():
                    topic = obj.topic_custom.strip()
                else:
                    try:
                        topic = obj.get_topic_display()
                    except Exception:
                        topic = obj.topic

                msg = (
                    "<b>📩 Новое уведомление</b>\n"
                    f"От: {who}\n"
                    f"Тема: {topic}\n"
                )
                tg_send_admin(msg)

            transaction.on_commit(_notify)

            messages.success(request, "Сообщение отправлено администрации.")
            return redirect("homepage")
    else:
        form = form_class()

    return render(request, "users/contact_admin.html", {"form": form})


@user_passes_test(_is_admin, login_url="account_login")
def admin_send_message(request):
    User = get_user_model()
    if request.method == "POST":
        form = AdminSendUserMessageForm(request.POST, request.FILES)
        if form.is_valid():
            send_to = form.cleaned_data["send_to"]
            recipient = form.cleaned_data["recipient"]
            recipients = form.cleaned_data["recipients"]

            topic = form.cleaned_data["topic"]
            topic_custom = (form.cleaned_data["topic_custom"] or "").strip()
            text = form.cleaned_data["text"]
            link = (form.cleaned_data["link"] or "").strip()
            image = form.cleaned_data["image"]

            if send_to == "all":
                qs = User.objects.filter(is_active=True).select_related("profile")
            elif send_to == "one":
                qs = [recipient]
            else:  # many
                qs = list(recipients)

            created = 0
            for u in qs:
                UserMessages.objects.create(
                    user=u,
                    sender="Администрация сайта",
                    topic=topic,
                    title=topic_custom if topic == "other" else "",  # "Кратко"
                    text=text,
                    link=link,
                    image=image if image else None,
                )
                created += 1

            messages.success(request, f"Отправлено уведомлений: {created}")
            return redirect("admin_messages_inbox")
    else:
        form = AdminSendUserMessageForm()

    return render(request, "users/admin_send_message.html", {"form": form})