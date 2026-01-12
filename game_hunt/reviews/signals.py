from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ReviewVote


@receiver(post_save, sender=ReviewVote)
def review_vote_saved(sender, instance, **kwargs):
    instance.review.recalc_liked_percent()


@receiver(post_delete, sender=ReviewVote)
def review_vote_deleted(sender, instance, **kwargs):
    instance.review.recalc_liked_percent()