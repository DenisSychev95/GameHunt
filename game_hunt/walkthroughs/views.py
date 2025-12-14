from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils.text import slugify

from .models import Walkthrough
from games.models import Game
from .forms import WalkthroughForm


def walkthrough_list(request):
    """
    Список прохождений, опционально фильтр по игре: ?game=<slug>
    """
    walkthroughs = Walkthrough.objects.select_related('game', 'author').filter(is_published=True)

    game_slug = request.GET.get('game')
    current_game = None
    if game_slug:
        current_game = get_object_or_404(Game, slug=game_slug)
        walkthroughs = walkthroughs.filter(game=current_game)

    paginator = Paginator(walkthroughs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'walkthroughs': page_obj.object_list,
        'page_obj': page_obj,
        'current_game': current_game,
    }
    return render(request, 'walkthroughs/walkthrough_list.html', context)


def walkthrough_detail(request, slug):
    walkthrough = get_object_or_404(
        Walkthrough.objects.select_related('game', 'author'),
        slug=slug,
        is_published=True
    )
    return render(request, 'walkthroughs/walkthrough_detail.html', {'walkthrough': walkthrough})


@login_required
def walkthrough_create(request, game_slug):
    game = get_object_or_404(Game, slug=game_slug)

    if request.method == 'POST':
        form = WalkthroughForm(request.POST)
        if form.is_valid():
            walkthrough = form.save(commit=False)
            walkthrough.game = game
            walkthrough.author = request.user
            # простой slug
            base_slug = slugify(form.cleaned_data['title'])[:200]
            slug = base_slug
            counter = 1
            while Walkthrough.objects.filter(slug=slug).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            walkthrough.slug = slug
            walkthrough.save()
            messages.success(request, 'Прохождение добавлено.')
            return redirect('walkthrough_detail', slug=walkthrough.slug)
    else:
        form = WalkthroughForm()

    return render(request, 'walkthroughs/walkthrough_form.html', {'form': form, 'game': game})