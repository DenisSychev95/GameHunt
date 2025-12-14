from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Cheat
from .forms import CheatForm
from games.models import Game


def cheat_list(request):
    cheats = Cheat.objects.select_related('game').filter(is_published=True)

    game_slug = request.GET.get('game')
    platform = request.GET.get('platform')

    current_game = None
    if game_slug:
        current_game = get_object_or_404(Game, slug=game_slug)
        cheats = cheats.filter(game=current_game)

    if platform:
        cheats = cheats.filter(platform=platform)

    paginator = Paginator(cheats, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'cheats': page_obj.object_list,
        'page_obj': page_obj,
        'current_game': current_game,
        'current_platform': platform,
    }
    return render(request, 'cheats/cheat_list.html', context)


def cheat_detail(request, pk):
    cheat = get_object_or_404(Cheat.objects.select_related('game'), pk=pk, is_published=True)
    return render(request, 'cheats/cheat_detail.html', {'cheat': cheat})


@login_required
def cheat_create(request, game_slug):
    game = get_object_or_404(Game, slug=game_slug)

    if request.method == 'POST':
        form = CheatForm(request.POST)
        if form.is_valid():
            cheat = form.save(commit=False)
            cheat.game = game
            cheat.save()
            messages.success(request, 'Чит добавлен.')
            return redirect('cheat_detail', pk=cheat.pk)
    else:
        form = CheatForm()

    return render(request, 'cheats/cheat_form.html', {'form': form, 'game': game})