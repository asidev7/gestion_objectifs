from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.utils.html import format_html
from .models import ProfilStagiaire, Tache, Semaine, SalaireMensuel, Evaluation


@admin.register(ProfilStagiaire)
class ProfilStagiaireAdmin(admin.ModelAdmin):
    list_display = [
        'nom_complet', 'etablissement', 'statut', 'niveau_competence',
        'taux_horaire', 'date_debut_stage', 'date_fin_stage', 'jours_restants_display'
    ]
    list_filter = ['statut', 'niveau_competence', 'date_debut_stage', 'etablissement']
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'etablissement']
    readonly_fields = ['date_creation', 'date_modification', 'age', 'duree_stage_jours']
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user', 'photo')
        }),
        ('Informations Personnelles', {
            'fields': (
                'telephone', 'date_naissance', 'adresse', 
                'ville', 'code_postal', 'pays'
            )
        }),
        ('Informations du Stage', {
            'fields': (
                'date_debut_stage', 'date_fin_stage', 'etablissement',
                'diplome_prepare', 'niveau_etude', 'domaine_specialisation'
            )
        }),
        ('Statut et Suivi', {
            'fields': ('statut', 'niveau_competence', 'tuteur')
        }),
        ('Informations Financières', {
            'fields': ('taux_horaire', 'heures_hebdomadaires')
        }),
        ('Compétences', {
            'fields': ('competences', 'objectifs_stage', 'notes_internes')
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def jours_restants_display(self, obj):
        jours = obj.jours_restants
        if jours == 0:
            return format_html('<span style="color: red;">Terminé</span>')
        elif jours <= 7:
            return format_html('<span style="color: orange;">{} jours</span>', jours)
        else:
            return format_html('<span style="color: green;">{} jours</span>', jours)
    jours_restants_display.short_description = 'Jours restants'


@admin.register(Tache)
class TacheAdmin(admin.ModelAdmin):
    list_display = [
        'titre', 'stagiaire', 'jour_semaine', 'priorite',
        'heures_effectuees', 'heures_estimees', 'pourcentage_display',
        'est_terminee', 'semaine_numero', 'annee'
    ]
    list_filter = [
        'est_terminee', 'jour_semaine', 'priorite', 
        'semaine_numero', 'annee', 'stagiaire'
    ]
    search_fields = ['titre', 'description', 'stagiaire__user__username']
    readonly_fields = ['date_creation', 'date_modification', 'date_completion', 'pourcentage_completion']
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('stagiaire', 'titre', 'description', 'priorite')
        }),
        ('Planification', {
            'fields': ('jour_semaine', 'semaine_numero', 'annee')
        }),
        ('Heures', {
            'fields': ('heures_estimees', 'heures_effectuees', 'pourcentage_completion')
        }),
        ('Suivi', {
            'fields': ('est_terminee', 'date_completion', 'remarques')
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['marquer_terminee', 'marquer_non_terminee']
    
    def pourcentage_display(self, obj):
        pct = obj.pourcentage_completion
        if pct >= 100:
            color = 'green'
        elif pct >= 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, pct
        )
    pourcentage_display.short_description = 'Progression'
    
    def marquer_terminee(self, request, queryset):
        from django.utils import timezone
        count = 0
        for tache in queryset:
            tache.est_terminee = True
            tache.date_completion = timezone.now()
            tache.heures_effectuees = tache.heures_estimees
            tache.save()
            count += 1
        self.message_user(request, f'{count} tâche(s) marquée(s) comme terminée(s).')
    marquer_terminee.short_description = 'Marquer comme terminée'
    
    def marquer_non_terminee(self, request, queryset):
        count = queryset.update(est_terminee=False, date_completion=None)
        self.message_user(request, f'{count} tâche(s) marquée(s) comme non terminée(s).')
    marquer_non_terminee.short_description = 'Marquer comme non terminée'


@admin.register(Semaine)
class SemaineAdmin(admin.ModelAdmin):
    list_display = [
        'stagiaire', 'numero_semaine', 'annee', 'date_debut', 'date_fin',
        'heures_totales', 'nombre_taches', 'taches_completees',
        'taux_completion_display', 'salaire_calcule'
    ]
    list_filter = ['annee', 'numero_semaine', 'stagiaire']
    search_fields = ['stagiaire__user__username']
    readonly_fields = [
        'date_creation', 'date_modification', 'taux_completion',
        'heures_totales', 'nombre_taches', 'taches_completees', 'salaire_calcule'
    ]
    
    fieldsets = (
        ('Stagiaire', {
            'fields': ('stagiaire',)
        }),
        ('Période', {
            'fields': ('numero_semaine', 'annee', 'date_debut', 'date_fin')
        }),
        ('Totaux (Calculés automatiquement)', {
            'fields': (
                'heures_totales', 'nombre_taches', 
                'taches_completees', 'taux_completion', 'salaire_calcule'
            )
        }),
        ('Commentaires', {
            'fields': ('commentaire_stagiaire', 'commentaire_tuteur', 'evaluation_tuteur')
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['recalculer_totaux']
    
    def taux_completion_display(self, obj):
        taux = obj.taux_completion
        if taux >= 80:
            color = 'green'
        elif taux >= 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, taux
        )
    taux_completion_display.short_description = 'Taux de complétion'
    
    def recalculer_totaux(self, request, queryset):
        count = 0
        for semaine in queryset:
            semaine.calculer_totaux()
            count += 1
        self.message_user(request, f'{count} semaine(s) recalculée(s).')
    recalculer_totaux.short_description = 'Recalculer les totaux'


@admin.register(SalaireMensuel)
class SalaireMensuelAdmin(admin.ModelAdmin):
    list_display = [
        'stagiaire', 'mois_display', 'annee', 'heures_totales',
        'salaire_brut', 'bonus', 'deductions', 'salaire_net',
        'est_paye', 'date_paiement'
    ]
    list_filter = ['annee', 'mois', 'est_paye', 'stagiaire']
    search_fields = ['stagiaire__user__username']
    readonly_fields = ['date_creation', 'date_modification', 'salaire_net']
    
    fieldsets = (
        ('Stagiaire et Période', {
            'fields': ('stagiaire', 'mois', 'annee')
        }),
        ('Heures et Salaire', {
            'fields': (
                'heures_totales', 'salaire_brut', 
                'bonus', 'deductions', 'salaire_net'
            )
        }),
        ('Paiement', {
            'fields': ('est_paye', 'date_paiement')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['marquer_paye', 'calculer_salaire_net']
    
    def mois_display(self, obj):
        import calendar
        return calendar.month_name[obj.mois]
    mois_display.short_description = 'Mois'
    
    def marquer_paye(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(est_paye=True, date_paiement=timezone.now().date())
        self.message_user(request, f'{count} salaire(s) marqué(s) comme payé(s).')
    marquer_paye.short_description = 'Marquer comme payé'
    
    def calculer_salaire_net(self, request, queryset):
        count = 0
        for salaire in queryset:
            salaire.calculer_salaire_net()
            count += 1
        self.message_user(request, f'{count} salaire(s) recalculé(s).')
    calculer_salaire_net.short_description = 'Recalculer le salaire net'


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = [
        'stagiaire', 'type_evaluation', 'date_evaluation',
        'evaluateur', 'note_moyenne_display',
        'competence_technique', 'qualite_travail'
    ]
    list_filter = ['type_evaluation', 'date_evaluation', 'stagiaire', 'evaluateur']
    search_fields = ['stagiaire__user__username', 'evaluateur__username']
    readonly_fields = ['date_creation', 'note_moyenne']
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('stagiaire', 'evaluateur', 'type_evaluation', 'date_evaluation')
        }),
        ('Critères d\'Évaluation (sur 5)', {
            'fields': (
                'competence_technique', 'qualite_travail',
                'autonomie', 'communication', 'respect_delais',
                'note_moyenne'
            )
        }),
        ('Commentaires', {
            'fields': (
                'points_forts', 'points_amelioration',
                'commentaire_general', 'objectifs_futurs'
            )
        }),
        ('Métadonnées', {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        }),
    )
    
    def note_moyenne_display(self, obj):
        note = obj.note_moyenne
        if note >= 4:
            color = 'green'
        elif note >= 3:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2f}/5</span>',
            color, note
        )
    note_moyenne_display.short_description = 'Note Moyenne'