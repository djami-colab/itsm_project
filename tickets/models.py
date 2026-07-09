from django.db import models
from django.contrib.auth.models import AbstractUser

class Role(models.Model):
    libelle = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.libelle

class Utilisateur(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    
    # We can add clean helper properties to check roles
    @property
    def is_client(self):
        return self.role and self.role.libelle == 'Client'

    @property
    def is_technicien(self):
        return self.role and self.role.libelle == 'Technicien'

    @property
    def is_admin(self):
        return self.role and self.role.libelle == 'Admin'

    def __str__(self):
        role_name = self.role.libelle if self.role else "Sans Rôle"
        return f"{self.username} ({role_name})"

class Categorie(models.Model):
    libelle = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.libelle

class Probleme(models.Model):
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, related_name='problemes')
    libelle = models.CharField(max_length=200)
    actif = models.BooleanField(default=True)

    def __str__(self):
        status = "Actif" if self.actif else "Inactif"
        return f"[{self.categorie.libelle}] {self.libelle} ({status})"

class Priorite(models.Model):
    libelle = models.CharField(max_length=50, unique=True)
    niveau = models.IntegerField(default=1)  # Pour trier par ordre d'urgence

    def __str__(self):
        return self.libelle

class StatutTicket(models.Model):
    libelle = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.libelle

class Ticket(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='tickets_crees')
    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT, related_name='tickets')
    probleme = models.ForeignKey(Probleme, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    probleme_autre = models.TextField(null=True, blank=True)
    priorite = models.ForeignKey(Priorite, on_delete=models.PROTECT, related_name='tickets')
    statut = models.ForeignKey(StatutTicket, on_delete=models.PROTECT, related_name='tickets')
    technicien = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_assignes')
    description = models.TextField(blank=True, default="")
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_assignation = models.DateTimeField(null=True, blank=True)
    date_resolution = models.DateTimeField(null=True, blank=True)
    date_cloture = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        prob = self.probleme.libelle if self.probleme else f"Autre : {self.probleme_autre[:30]}"
        return f"Ticket #{self.id} - {self.categorie.libelle} ({prob}) - {self.statut.libelle}"

class PieceJointe(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='pieces_jointes')
    fichier = models.FileField(upload_to='ticket_attachments/')
    nom_original = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='pieces_jointes')
    date_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PJ #{self.id} pour Ticket #{self.ticket.id} ({self.nom_original})"

class HistoriqueTicket(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='historiques')
    ancien_statut = models.ForeignKey(StatutTicket, on_delete=models.SET_NULL, null=True, related_name='historiques_anciens')
    nouveau_statut = models.ForeignKey(StatutTicket, on_delete=models.SET_NULL, null=True, related_name='historiques_nouveaux')
    modifie_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='historiques_modifications')
    date_modification = models.DateTimeField(auto_now_add=True)
    commentaire = models.TextField(null=True, blank=True)

    def __str__(self):
        anc = self.ancien_statut.libelle if self.ancien_statut else "N/A"
        nouveau = self.nouveau_statut.libelle if self.nouveau_statut else "N/A"
        return f"Hist #{self.id} Ticket #{self.ticket.id}: {anc} -> {nouveau} le {self.date_modification.strftime('%d/%m/%Y %H:%M')}"
