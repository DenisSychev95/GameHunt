from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import WalkthroughVote


@receiver(post_save, sender=WalkthroughVote)
def walkthrough_vote_saved(sender, instance, **kwargs):
    instance.walkthrough.recalc_liked_percent()


@receiver(post_delete, sender=WalkthroughVote)
def walkthrough_vote_deleted(sender, instance, **kwargs):
    instance.walkthrough.recalc_liked_percent()