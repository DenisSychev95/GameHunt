from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def profile(request):
    account_profile = request.user.profile
    context = {
        'profile': account_profile
    }
    return render(request, 'accounts/profile.html', context)


