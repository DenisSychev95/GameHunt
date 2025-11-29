from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ProfileEditForm
from django.contrib import messages


@login_required(login_url='account_login')
def profile(request):
    account_profile = request.user.profile
    context = {
        'profile': account_profile
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
