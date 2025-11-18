from django.shortcuts import render


def homepage(request):
    return render(request, 'home.html')


def about(request):
    return render(request, 'core/about.html')


def contacts(request):
    return render(request, 'core/contacts.html')


def privacy_policy(request):
    return render(request, 'core/privacy_policy.html')
