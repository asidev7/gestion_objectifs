from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal


# Page de connexion
def connexion_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect(dashboard_stagiaire)
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect")
    return render(request, 'auth/login.html')

# Déconnexion
@login_required
def deconnexion_view(request):
    logout(request)
    return redirect('connexion')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta
import calendar

from .models import ProfilStagiaire, Tache, Semaine, SalaireMensuel, Evaluation


@login_required
def dashboard_stagiaire(request):
    """Vue principale du dashboard pour un stagiaire"""
    
    try:
        profil = request.user.profil_stagiaire
    except ProfilStagiaire.DoesNotExist:
        messages.error(request, "Profil stagiaire non trouvé.")
        return redirect('home')
    
    # Date actuelle et semaine
    today = timezone.now().date()
    current_week = today.isocalendar()[1]
    current_year = today.year
    current_month = today.month
    
    # Obtenir ou créer la semaine courante
    semaine_debut = today - timedelta(days=today.weekday())
    semaine_fin = semaine_debut + timedelta(days=5)  # Jusqu'à samedi
    
    semaine_actuelle, created = Semaine.objects.get_or_create(
        stagiaire=profil,
        numero_semaine=current_week,
        annee=current_year,
        defaults={
            'date_debut': semaine_debut,
            'date_fin': semaine_fin,
        }
    )
    
    # Calculer les totaux de la semaine
    semaine_actuelle.calculer_totaux()
    
    # Tâches de la semaine groupées par jour
    taches_semaine = Tache.objects.filter(
        stagiaire=profil,
        semaine_numero=current_week,
        annee=current_year
    ).order_by('jour_semaine', '-priorite')
    
    # Organiser les tâches par jour
    jours = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi']
    taches_par_jour = {}
    heures_par_jour = {}
    
    for jour in jours:
        taches_jour = taches_semaine.filter(jour_semaine=jour)
        taches_par_jour[jour] = taches_jour
        heures_par_jour[jour] = sum(float(t.heures_effectuees) for t in taches_jour)
    
    # Statistiques du mois
    salaire_mois, created = SalaireMensuel.objects.get_or_create(
        stagiaire=profil,
        mois=current_month,
        annee=current_year
    )
    
    # Calculer heures et salaire du mois
    taches_mois = Tache.objects.filter(
        stagiaire=profil,
        annee=current_year,
        semaine_numero__in=get_weeks_in_month(current_year, current_month)
    )
    
    heures_mois = sum(Decimal(t.heures_effectuees) for t in taches_mois)

    # Stocker dans salaire_mois
    salaire_mois.heures_totales = heures_mois
    # Salaire brut = heures * taux horaire (Decimal * Decimal)
    salaire_mois.salaire_brut = heures_mois * profil.taux_horaire
    # Calcul du salaire net
    salaire_mois.calculer_salaire_net()
    # Calculer le trimestre (T1, T2, T3, T4)
    trimestre = ((current_month - 1) // 3) + 1
    mois_trimestre = [(trimestre - 1) * 3 + i for i in range(1, 4)]
    
    # Heures et salaire du trimestre
    heures_trimestre = 0
    salaire_trimestre = 0
    
    for mois in mois_trimestre:
        if mois <= 12:
            weeks = get_weeks_in_month(current_year, mois)
            taches_mois_t = Tache.objects.filter(
                stagiaire=profil,
                annee=current_year,
                semaine_numero__in=weeks
            )
            heures_t = sum(float(t.heures_effectuees) for t in taches_mois_t)
            heures_trimestre += heures_t
    
    salaire_trimestre = heures_trimestre * float(profil.taux_horaire)
    
    # Statistiques générales
    total_taches = taches_semaine.count()
    taches_completees = taches_semaine.filter(est_terminee=True).count()
    taches_en_cours = total_taches - taches_completees
    
    # Progression
    progression = (taches_completees / total_taches * 100) if total_taches > 0 else 0
    
    # Dernière évaluation
    derniere_eval = Evaluation.objects.filter(stagiaire=profil).first()
    
    context = {
        'profil': profil,
        'semaine_actuelle': semaine_actuelle,
        'taches_par_jour': taches_par_jour,
        'heures_par_jour': heures_par_jour,
        'jours': jours,
        'jours_labels': {
            'lundi': 'Lundi',
            'mardi': 'Mardi',
            'mercredi': 'Mercredi',
            'jeudi': 'Jeudi',
            'vendredi': 'Vendredi',
            'samedi': 'Samedi',
        },
        
        # Stats semaine
        'heures_semaine': semaine_actuelle.heures_totales,
        'taches_semaine': total_taches,
        'taches_completees': taches_completees,
        'taches_en_cours': taches_en_cours,
        'progression': progression,
        'salaire_semaine': semaine_actuelle.salaire_calcule,
        
        # Stats mois
        'heures_mois': heures_mois,
        'salaire_mois': salaire_mois.salaire_net,
        'mois_nom': calendar.month_name[current_month],
        
        # Stats trimestre
        'heures_trimestre': heures_trimestre,
        'salaire_trimestre': salaire_trimestre,
        'trimestre': trimestre,
        'trimestre_label': f'T{trimestre} {current_year}',
        
        # Infos semaine
        'semaine_numero': current_week,
        'annee': current_year,
        'date_debut': semaine_debut,
        'date_fin': semaine_fin,
        
        # Évaluation
        'derniere_eval': derniere_eval,
        
        # Dates
        'today': today,
    }
    
    return render(request, 'stagiaires/dashboard.html', context)


@login_required
def ajouter_tache(request):
    """Ajouter une nouvelle tâche"""
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        profil = request.user.profil_stagiaire
    except ProfilStagiaire.DoesNotExist:
        return JsonResponse({'error': 'Profil non trouvé'}, status=404)
    
    # Récupérer les données
    titre = request.POST.get('titre')
    description = request.POST.get('description', '')
    jour_semaine = request.POST.get('jour_semaine')
    heures_estimees = request.POST.get('heures_estimees')
    heures_effectuees = request.POST.get('heures_effectuees', 0)
    remarques = request.POST.get('remarques', '')
    priorite = request.POST.get('priorite', 'moyenne')
    
    # Validation
    if not all([titre, jour_semaine, heures_estimees]):
        return JsonResponse({'error': 'Champs obligatoires manquants'}, status=400)
    
    # Date et semaine
    today = timezone.now().date()
    current_week = today.isocalendar()[1]
    current_year = today.year
    
    # Créer la tâche
    tache = Tache.objects.create(
        stagiaire=profil,
        titre=titre,
        description=description,
        jour_semaine=jour_semaine.lower(),
        heures_estimees=float(heures_estimees),
        heures_effectuees=float(heures_effectuees),
        remarques=remarques,
        priorite=priorite,
        semaine_numero=current_week,
        annee=current_year,
        est_terminee=(float(heures_effectuees) >= float(heures_estimees))
    )
    
    # Mettre à jour la semaine
    semaine_debut = today - timedelta(days=today.weekday())
    semaine_fin = semaine_debut + timedelta(days=5)
    
    semaine, created = Semaine.objects.get_or_create(
        stagiaire=profil,
        numero_semaine=current_week,
        annee=current_year,
        defaults={
            'date_debut': semaine_debut,
            'date_fin': semaine_fin,
        }
    )
    semaine.calculer_totaux()
    
    messages.success(request, 'Tâche ajoutée avec succès!')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Tâche ajoutée avec succès!',
            'tache_id': tache.id
        })
    
    return redirect(dashboard_stagiaire)


@login_required
def ajouter_heures(request, tache_id):
    """Ajouter des heures à une tâche existante"""
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    tache = get_object_or_404(Tache, id=tache_id, stagiaire=request.user.profil_stagiaire)
    
    heures = float(request.POST.get('heures', 0))
    
    if heures <= 0:
        return JsonResponse({'error': 'Nombre d\'heures invalide'}, status=400)
    
    # Ajouter les heures
    tache.ajouter_heures(heures)
    
    # Mettre à jour la semaine
    semaine = Semaine.objects.filter(
        stagiaire=tache.stagiaire,
        numero_semaine=tache.semaine_numero,
        annee=tache.annee
    ).first()
    
    if semaine:
        semaine.calculer_totaux()
    
    messages.success(request, f'{heures}h ajoutée(s) à la tâche!')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'heures_effectuees': float(tache.heures_effectuees),
            'pourcentage': tache.pourcentage_completion,
            'est_terminee': tache.est_terminee
        })
    
    return redirect(dashboard_stagiaire)


@login_required
def supprimer_tache(request, tache_id):
    """Supprimer une tâche"""
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    tache = get_object_or_404(Tache, id=tache_id, stagiaire=request.user.profil_stagiaire)
    
    # Sauvegarder les infos avant suppression
    semaine_num = tache.semaine_numero
    annee = tache.annee
    stagiaire = tache.stagiaire
    
    tache.delete()
    
    # Mettre à jour la semaine
    semaine = Semaine.objects.filter(
        stagiaire=stagiaire,
        numero_semaine=semaine_num,
        annee=annee
    ).first()
    
    if semaine:
        semaine.calculer_totaux()
    
    messages.success(request, 'Tâche supprimée avec succès!')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect(dashboard_stagiaire)


@login_required
def toggle_tache(request, tache_id):
    """Marquer une tâche comme terminée/non terminée"""
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    tache = get_object_or_404(Tache, id=tache_id, stagiaire=request.user.profil_stagiaire)
    
    tache.est_terminee = not tache.est_terminee
    
    if tache.est_terminee:
        tache.date_completion = timezone.now()
        # Mettre les heures effectuées = heures estimées si terminée
        if tache.heures_effectuees < tache.heures_estimees:
            tache.heures_effectuees = tache.heures_estimees
    else:
        tache.date_completion = None
    
    tache.save()
    
    # Mettre à jour la semaine
    semaine = Semaine.objects.filter(
        stagiaire=tache.stagiaire,
        numero_semaine=tache.semaine_numero,
        annee=tache.annee
    ).first()
    
    if semaine:
        semaine.calculer_totaux()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'est_terminee': tache.est_terminee
        })
    
    return redirect(dashboard_stagiaire)


@login_required
def semaine_details(request, semaine_id):
    """Détails d'une semaine spécifique"""
    
    semaine = get_object_or_404(
        Semaine, 
        id=semaine_id, 
        stagiaire=request.user.profil_stagiaire
    )
    
    taches = Tache.objects.filter(
        stagiaire=semaine.stagiaire,
        semaine_numero=semaine.numero_semaine,
        annee=semaine.annee
    ).order_by('jour_semaine', '-priorite')
    
    context = {
        'semaine': semaine,
        'taches': taches,
    }
    
    return render(request, 'stagiaires/semaine_details.html', context)


@login_required
def historique_semaines(request):
    """Historique de toutes les semaines"""
    
    profil = request.user.profil_stagiaire
    
    semaines = Semaine.objects.filter(stagiaire=profil).order_by('-annee', '-numero_semaine')
    
    # Statistiques globales
    total_heures = semaines.aggregate(Sum('heures_totales'))['heures_totales__sum'] or 0
    total_salaire = semaines.aggregate(Sum('salaire_calcule'))['salaire_calcule__sum'] or 0
    moyenne_heures = semaines.aggregate(Avg('heures_totales'))['heures_totales__avg'] or 0
    
    context = {
        'semaines': semaines,
        'total_heures': total_heures,
        'total_salaire': total_salaire,
        'moyenne_heures': round(moyenne_heures, 2),
    }
    
    return render(request, 'stagiaires/historique.html', context)


@login_required
def profil_stagiaire(request):
    """Voir et modifier le profil"""
    
    profil = request.user.profil_stagiaire
    
    if request.method == 'POST':
        # Mise à jour du profil
        profil.telephone = request.POST.get('telephone', profil.telephone)
        profil.adresse = request.POST.get('adresse', profil.adresse)
        profil.ville = request.POST.get('ville', profil.ville)
        profil.code_postal = request.POST.get('code_postal', profil.code_postal)
        
        if 'photo' in request.FILES:
            profil.photo = request.FILES['photo']
        
        profil.save()
        messages.success(request, 'Profil mis à jour avec succès!')
        return redirect('profil_stagiaire')
    
    # Statistiques du profil
    total_taches = Tache.objects.filter(stagiaire=profil).count()
    taches_terminees = Tache.objects.filter(stagiaire=profil, est_terminee=True).count()
    total_heures = Tache.objects.filter(stagiaire=profil).aggregate(
        Sum('heures_effectuees')
    )['heures_effectuees__sum'] or 0
    
    evaluations = Evaluation.objects.filter(stagiaire=profil).order_by('-date_evaluation')[:5]
    
    context = {
        'profil': profil,
        'total_taches': total_taches,
        'taches_terminees': taches_terminees,
        'total_heures': total_heures,
        'evaluations': evaluations,
    }
    
    return render(request, 'stagiaires/profil.html', context)


def get_weeks_in_month(year, month):
    """Retourne les numéros de semaines dans un mois donné"""
    first_day = datetime(year, month, 1).date()
    if month == 12:
        last_day = datetime(year, 12, 31).date()
    else:
        last_day = (datetime(year, month + 1, 1) - timedelta(days=1)).date()
    
    weeks = set()
    current = first_day
    while current <= last_day:
        weeks.add(current.isocalendar()[1])
        current += timedelta(days=1)
    
    return list(weeks)


# Vue pour les superviseurs/tuteurs
@login_required
def dashboard_superviseur(request):
    """Dashboard pour les superviseurs/tuteurs"""
    
    # Récupérer tous les stagiaires supervisés
    stagiaires = ProfilStagiaire.objects.filter(tuteur=request.user)
    
    today = timezone.now().date()
    current_week = today.isocalendar()[1]
    current_year = today.year
    
    # Statistiques globales
    stats = []
    for stagiaire in stagiaires:
        semaine = Semaine.objects.filter(
            stagiaire=stagiaire,
            numero_semaine=current_week,
            annee=current_year
        ).first()
        
        if semaine:
            semaine.calculer_totaux()
        
        taches_total = Tache.objects.filter(stagiaire=stagiaire).count()
        taches_terminees = Tache.objects.filter(
            stagiaire=stagiaire, 
            est_terminee=True
        ).count()
        
        stats.append({
            'stagiaire': stagiaire,
            'semaine': semaine,
            'taches_total': taches_total,
            'taches_terminees': taches_terminees,
            'progression': (taches_terminees / taches_total * 100) if taches_total > 0 else 0
        })
    
    context = {
        'stagiaires': stagiaires,
        'stats': stats,
        'semaine_numero': current_week,
    }
    
    return render(request, 'stagiaires/dashboard_superviseur.html', context)


@login_required
def evaluer_stagiaire(request, stagiaire_id):
    """Créer une évaluation pour un stagiaire"""
    
    stagiaire = get_object_or_404(ProfilStagiaire, id=stagiaire_id, tuteur=request.user)
    
    if request.method == 'POST':
        evaluation = Evaluation.objects.create(
            stagiaire=stagiaire,
            evaluateur=request.user,
            type_evaluation=request.POST.get('type_evaluation'),
            competence_technique=int(request.POST.get('competence_technique')),
            qualite_travail=int(request.POST.get('qualite_travail')),
            autonomie=int(request.POST.get('autonomie')),
            communication=int(request.POST.get('communication')),
            respect_delais=int(request.POST.get('respect_delais')),
            points_forts=request.POST.get('points_forts', ''),
            points_amelioration=request.POST.get('points_amelioration', ''),
            commentaire_general=request.POST.get('commentaire_general', ''),
            objectifs_futurs=request.POST.get('objectifs_futurs', ''),
        )
        
        messages.success(request, 'Évaluation créée avec succès!')
        return redirect(dashboard_superviseur)
    
    context = {
        'stagiaire': stagiaire,
    }
    
    return render(request, 'stagiaires/evaluer.html', context)