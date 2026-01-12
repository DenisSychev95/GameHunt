from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .forms import ProfileEditForm
from django.contrib import messages
from .models import Profile


@login_required(login_url='account_login')
def profile(request):
    account_profile = request.user.profile
    context = {
        'profile': account_profile
    }
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
