from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import ProfilStagiaire
from django.utils import timezone

@receiver(post_save, sender=User)
def creer_profil_stagiaire(sender, instance, created, **kwargs):
    """
    Crée automatiquement un ProfilStagiaire à la création d'un User.
    """
    if created:
        ProfilStagiaire.objects.create(
            user=instance,
            date_debut_stage=timezone.now().date(),  # tu peux adapter par défaut
            date_fin_stage=timezone.now().date() + timezone.timedelta(days=90)  # exemple 3 mois
        )
