from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from tickets.models import Role, Categorie, Probleme, Priorite, StatutTicket, Ticket, HistoriqueTicket

# Monkey patch for Python 3.14 / Django 5.1 compatibility issue in test client copy(context)
from django.template.context import BaseContext
def custom_context_copy(self):
    duplicate = BaseContext()
    duplicate.dicts = self.dicts[:]
    return duplicate
BaseContext.__copy__ = custom_context_copy

Utilisateur = get_user_model()

class ITSMModelTests(TestCase):
    def setUp(self):
        # Base setup
        self.role_client = Role.objects.create(libelle='Client')
        self.role_tech = Role.objects.create(libelle='Technicien')
        self.role_admin = Role.objects.create(libelle='Admin')

        self.client_user = Utilisateur.objects.create_user(
            username='test_client',
            password='password123',
            role=self.role_client
        )
        
        self.tech_user = Utilisateur.objects.create_user(
            username='test_tech',
            password='password123',
            role=self.role_tech
        )

        self.cat_reseau = Categorie.objects.create(libelle='Réseau')
        self.prio_moyenne = Priorite.objects.create(libelle='Moyenne', niveau=2)
        self.statut_nouveau = StatutTicket.objects.create(libelle='Nouveau')
        self.statut_assigne = StatutTicket.objects.create(libelle='Assigné')

        self.problem = Probleme.objects.create(
            categorie=self.cat_reseau,
            libelle="Panne Wi-Fi",
            actif=True
        )

    def test_user_role_properties(self):
        """Test user helper properties for roles"""
        self.assertTrue(self.client_user.is_client)
        self.assertFalse(self.client_user.is_technicien)
        self.assertFalse(self.client_user.is_admin)

        self.assertTrue(self.tech_user.is_technicien)
        self.assertFalse(self.tech_user.is_client)

    def test_ticket_creation(self):
        """Test creating a ticket and check relationships"""
        ticket = Ticket.objects.create(
            utilisateur=self.client_user,
            categorie=self.cat_reseau,
            probleme=self.problem,
            priorite=self.prio_moyenne,
            statut=self.statut_nouveau,
            description="Le Wi-Fi ne fonctionne pas dans la salle de réunion."
        )

        self.assertEqual(ticket.utilisateur.username, 'test_client')
        self.assertEqual(ticket.categorie.libelle, 'Réseau')
        self.assertEqual(ticket.probleme.libelle, 'Panne Wi-Fi')
        self.assertNil = self.assertIsNone(ticket.technicien)
        self.assertEqual(str(ticket), f"Ticket #{ticket.id} - Réseau (Panne Wi-Fi) - Nouveau")

    def test_redirection_based_on_role(self):
        """Test login and redirection based on user roles"""
        # Client login
        login_success = self.client.login(username='test_client', password='password123')
        self.assertTrue(login_success)
        
        response = self.client.get(reverse('dashboard'))
        # Should redirect to client_dashboard
        self.assertRedirects(response, reverse('client_dashboard'))

        self.client.logout()

        # Technician login
        login_success = self.client.login(username='test_tech', password='password123')
        self.assertTrue(login_success)
        
        response = self.client.get(reverse('dashboard'))
        # Should redirect to admin_dashboard
        self.assertRedirects(response, reverse('admin_dashboard'))
