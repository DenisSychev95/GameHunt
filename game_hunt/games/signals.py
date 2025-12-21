from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import GameVote


@receiver(post_save, sender=GameVote)
def update_game_likes_on_save(sender, instance, **kwargs):
    instance.game.recalc_liked_percent()


@receiver(post_delete, sender=GameVote)
def update_game_likes_on_delete(sender, instance, **kwargs):
    instance.game.recalc_liked_percent()
