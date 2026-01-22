
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard stagiaire
    
    
    path('login/', views.connexion_view, name='connexion'),
    path('logout/', views.deconnexion_view, name='deconnexion'),
    
    path('', views.dashboard_stagiaire, name='dashboard_stagiaire'),
    path('profil/', views.profil_stagiaire, name='profil_stagiaire'),
    
    # Gestion des tâches
    path('tache/ajouter/', views.ajouter_tache, name='ajouter_tache'),
    path('tache/<int:tache_id>/ajouter-heures/', views.ajouter_heures, name='ajouter_heures'),
    path('tache/<int:tache_id>/supprimer/', views.supprimer_tache, name='supprimer_tache'),
    path('tache/<int:tache_id>/toggle/', views.toggle_tache, name='toggle_tache'),
    
    # Semaines
    path('semaine/<int:semaine_id>/', views.semaine_details, name='semaine_details'),
    path('historique/', views.historique_semaines, name='historique_semaines'),
    
    # Dashboard superviseur
    path('superviseur/', views.dashboard_superviseur, name='dashboard_superviseur'),
    path('superviseur/evaluer/<int:stagiaire_id>/', views.evaluer_stagiaire, name='evaluer_stagiaire'),
]
