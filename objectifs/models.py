from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal, InvalidOperation


class ProfilStagiaire(models.Model):
    """Profil étendu pour les stagiaires"""
    
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('termine', 'Terminé'),
        ('suspendu', 'Suspendu'),
    ]
    
    NIVEAU_CHOICES = [
        ('debutant', 'Débutant'),
        ('intermediaire', 'Intermédiaire'),
        ('avance', 'Avancé'),
    ]
    
    # Relation avec User
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil_stagiaire')
    
    # Informations personnelles
    photo = models.ImageField(upload_to='stagiaires/photos/', blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True)
    date_naissance = models.DateField(blank=True, null=True)
    adresse = models.TextField(blank=True)
    ville = models.CharField(max_length=100, blank=True)
    code_postal = models.CharField(max_length=10, blank=True)
    pays = models.CharField(max_length=100, default='Bénin')
    
    # Informations du stage
    date_debut_stage = models.DateField()
    date_fin_stage = models.DateField()
    etablissement = models.CharField(max_length=200, help_text="École ou université d'origine")
    diplome_prepare = models.CharField(max_length=200, blank=True)
    niveau_etude = models.CharField(max_length=100, blank=True)
    domaine_specialisation = models.CharField(max_length=200, blank=True)
    
    # Statut et suivi
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif')
    niveau_competence = models.CharField(max_length=20, choices=NIVEAU_CHOICES, default='debutant')
    tuteur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                               related_name='stagiaires_supervises',
                               help_text="Responsable qui supervise le stagiaire")
    
    # Informations financières
    taux_horaire = models.DecimalField(max_digits=6, decimal_places=2, default=6.69,
                                       validators=[MinValueValidator(0)])
    heures_hebdomadaires = models.PositiveIntegerField(default=35,
                                                       help_text="Nombre d'heures par semaine")
    
    # Compétences et notes
    competences = models.TextField(blank=True, help_text="Compétences du stagiaire (séparées par des virgules)")
    objectifs_stage = models.TextField(blank=True, help_text="Objectifs à atteindre pendant le stage")
    notes_internes = models.TextField(blank=True, help_text="Notes internes sur le stagiaire")
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Profil Stagiaire"
        verbose_name_plural = "Profils Stagiaires"
        ordering = ['-date_debut_stage']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.etablissement}"
    
    @property
    def nom_complet(self):
        return self.user.get_full_name() or self.user.username
    
    @property
    def age(self):
        if self.date_naissance:
            today = timezone.now().date()
            return today.year - self.date_naissance.year - (
                (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day)
            )
        return None
    
    @property
    def duree_stage_jours(self):
        return (self.date_fin_stage - self.date_debut_stage).days
    
    @property
    def jours_restants(self):
        today = timezone.now().date()
        if today > self.date_fin_stage:
            return 0
        return (self.date_fin_stage - today).days
    
    @property
    def est_actif(self):
        today = timezone.now().date()
        return (self.statut == 'actif' and 
                self.date_debut_stage <= today <= self.date_fin_stage)


class Tache(models.Model):
    """Tâches assignées aux stagiaires"""

    JOUR_SEMAINE_CHOICES = [
        ('lundi', 'Lundi'),
        ('mardi', 'Mardi'),
        ('mercredi', 'Mercredi'),
        ('jeudi', 'Jeudi'),
        ('vendredi', 'Vendredi'),
        ('samedi', 'Samedi'),
    ]

    PRIORITE_CHOICES = [
        ('basse', 'Basse'),
        ('moyenne', 'Moyenne'),
        ('haute', 'Haute'),
        ('urgente', 'Urgente'),
    ]

    # Relations
    stagiaire = models.ForeignKey(
        ProfilStagiaire,
        on_delete=models.CASCADE,
        related_name='taches'
    )

    # Infos tâche
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    jour_semaine = models.CharField(
        max_length=20,
        choices=JOUR_SEMAINE_CHOICES
    )
    priorite = models.CharField(
        max_length=20,
        choices=PRIORITE_CHOICES,
        default='moyenne'
    )

    # Heures (DECIMAL CLEAN)
    heures_estimees = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.10"))]
    )

    heures_effectuees = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )

    # Dates
    semaine_numero = models.PositiveIntegerField(
        help_text="Numéro de la semaine dans l'année"
    )
    annee = models.PositiveIntegerField()
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    date_completion = models.DateTimeField(null=True, blank=True)

    # Suivi
    est_terminee = models.BooleanField(default=False)
    remarques = models.TextField(blank=True)

    class Meta:
        verbose_name = "Tâche"
        verbose_name_plural = "Tâches"
        ordering = ['annee', 'semaine_numero', 'jour_semaine', '-priorite']
        indexes = [
            models.Index(fields=['stagiaire', 'semaine_numero', 'annee']),
            models.Index(fields=['est_terminee']),
        ]

    def __str__(self):
        return f"{self.titre} - {self.stagiaire.nom_complet} ({self.jour_semaine})"

    # ==========================
    # 🔢 PROPRIÉTÉS MÉTIER
    # ==========================

    @property
    def pourcentage_completion(self) -> Decimal:
        """Retourne le pourcentage d'avancement (0 → 100)"""
        if self.heures_estimees > Decimal("0"):
            pourcentage = (self.heures_effectuees / self.heures_estimees) * Decimal("100")
            return min(pourcentage, Decimal("100"))
        return Decimal("0")

    @property
    def heures_restantes(self) -> Decimal:
        """Heures restantes (jamais négatif)"""
        reste = self.heures_estimees - self.heures_effectuees
        return max(reste, Decimal("0"))

    # ==========================
    # ⏱️ MÉTHODES MÉTIER
    # ==========================

    def ajouter_heures(self, heures):
        """
        Ajoute des heures effectuées de manière sécurisée
        """
        try:
            heures = Decimal(heures)
        except (InvalidOperation, TypeError):
            raise ValueError("Heures invalides")

        if heures <= Decimal("0"):
            raise ValueError("Les heures doivent être supérieures à 0")

        # Sécurité
        if self.heures_effectuees is None:
            self.heures_effectuees = Decimal("0")

        self.heures_effectuees += heures

        # Terminaison auto
        if self.heures_effectuees >= self.heures_estimees:
            self.est_terminee = True
            if not self.date_completion:
                self.date_completion = timezone.now()

        self.save(update_fields=[
            "heures_effectuees",
            "est_terminee",
            "date_completion",
            "date_modification"
        ])

class Semaine(models.Model):
    """Suivi des semaines de travail"""
    
    stagiaire = models.ForeignKey(ProfilStagiaire, on_delete=models.CASCADE, related_name='semaines')
    
    # Identification de la semaine
    numero_semaine = models.PositiveIntegerField()
    annee = models.PositiveIntegerField()
    date_debut = models.DateField()
    date_fin = models.DateField()
    
    # Totaux
    heures_totales = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    nombre_taches = models.PositiveIntegerField(default=0)
    taches_completees = models.PositiveIntegerField(default=0)
    
    # Salaire
    salaire_calcule = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Notes
    commentaire_stagiaire = models.TextField(blank=True)
    commentaire_tuteur = models.TextField(blank=True)
    evaluation_tuteur = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Évaluation sur 5"
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Semaine"
        verbose_name_plural = "Semaines"
        ordering = ['-annee', '-numero_semaine']
        unique_together = ['stagiaire', 'numero_semaine', 'annee']
        indexes = [
            models.Index(fields=['stagiaire', 'annee', 'numero_semaine']),
        ]
    
    def __str__(self):
        return f"Semaine {self.numero_semaine} - {self.annee} - {self.stagiaire.nom_complet}"
    
    @property
    def taux_completion(self):
        if self.nombre_taches > 0:
            return (self.taches_completees / self.nombre_taches) * 100
        return 0
    
    def calculer_totaux(self):
        """Calcule les totaux de la semaine à partir des tâches"""
        taches = Tache.objects.filter(
            stagiaire=self.stagiaire,
            semaine_numero=self.numero_semaine,
            annee=self.annee
        )
        
        self.nombre_taches = taches.count()
        self.taches_completees = taches.filter(est_terminee=True).count()
        self.heures_totales = sum(float(t.heures_effectuees) for t in taches)
        self.salaire_calcule = self.heures_totales * float(self.stagiaire.taux_horaire)
        self.save()


class SalaireMensuel(models.Model):
    """Calcul des salaires mensuels"""
    
    stagiaire = models.ForeignKey(ProfilStagiaire, on_delete=models.CASCADE, related_name='salaires_mensuels')
    
    # Période
    mois = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    annee = models.PositiveIntegerField()
    
    # Heures et salaire
    heures_totales = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    salaire_brut = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Bonus/Déductions
    bonus = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    salaire_net = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Statut
    est_paye = models.BooleanField(default=False)
    date_paiement = models.DateField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Salaire Mensuel"
        verbose_name_plural = "Salaires Mensuels"
        ordering = ['-annee', '-mois']
        unique_together = ['stagiaire', 'mois', 'annee']
    
    def __str__(self):
        return f"{self.stagiaire.nom_complet} - {self.mois}/{self.annee} - {self.salaire_net}€"
    
    def calculer_salaire_net(self):
        """Calcule le salaire net avec bonus et déductions"""
        self.salaire_net = self.salaire_brut + self.bonus - self.deductions
        self.save()


class Evaluation(models.Model):
    """Évaluations périodiques des stagiaires"""
    
    TYPE_CHOICES = [
        ('hebdomadaire', 'Hebdomadaire'),
        ('mensuelle', 'Mensuelle'),
        ('trimestrielle', 'Trimestrielle'),
        ('finale', 'Finale'),
    ]
    
    stagiaire = models.ForeignKey(ProfilStagiaire, on_delete=models.CASCADE, related_name='evaluations')
    evaluateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='evaluations_donnees')
    
    # Type et période
    type_evaluation = models.CharField(max_length=20, choices=TYPE_CHOICES)
    date_evaluation = models.DateField(default=timezone.now)
    
    # Critères (sur 5)
    competence_technique = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    qualite_travail = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    autonomie = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    communication = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    respect_delais = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Commentaires
    points_forts = models.TextField(blank=True)
    points_amelioration = models.TextField(blank=True)
    commentaire_general = models.TextField(blank=True)
    objectifs_futurs = models.TextField(blank=True)
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Évaluation"
        verbose_name_plural = "Évaluations"
        ordering = ['-date_evaluation']
    
    def __str__(self):
        return f"Évaluation {self.type_evaluation} - {self.stagiaire.nom_complet} - {self.date_evaluation}"
    
    @property
    def note_moyenne(self):
        return (self.competence_technique + self.qualite_travail + 
                self.autonomie + self.communication + self.respect_delais) / 5