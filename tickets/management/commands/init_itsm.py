from django.core.management.base import BaseCommand
from tickets.models import Role, Categorie, Probleme, Priorite, StatutTicket, Utilisateur

class Command(BaseCommand):
    help = "Initialise les données ITSM de base (Rôles, Catégories, Problèmes, Priorités, Statuts, Utilisateurs)"

    def handle(self, *args, **options):
        self.stdout.write("Initialisation des données ITSM...")

        # 1. Création des Rôles
        roles_data = ['Client', 'Technicien', 'Admin']
        roles = {}
        for r_name in roles_data:
            role, created = Role.objects.get_or_create(libelle=r_name)
            roles[r_name] = role
            if created:
                self.stdout.write(f"Rôle créé : {r_name}")

        # 2. Création des Catégories et Problèmes prédéfinis
        categories_problems = {
            'Réseau': [
                "Pas d'accès internet",
                "Connexion Wi-Fi instable",
                "Problème VPN",
                "Lenteur réseau"
            ],
            'Matériel': [
                "L'ordinateur ne s'allume pas",
                "Écran noir / défaillant",
                "Clavier / Souris défectueux",
                "Batterie ne charge pas"
            ],
            'Logiciel': [
                "Application plante au démarrage",
                "Problème avec Microsoft Office",
                "Antivirus bloquant",
                "Besoin de mise à jour"
            ],
            'Imprimante/Scanner': [
                "Bourrage papier",
                "Non détecté par l'ordinateur",
                "Impression de mauvaise qualité",
                "Scanner bloqué"
            ],
            'Demande': [
                "Accès à un dossier partagé",
                "Demande d'installation de logiciel",
                "Création de compte",
                "Matériel temporaire de prêt"
            ]
        }

        for cat_name, probs in categories_problems.items():
            category, created = Categorie.objects.get_or_create(libelle=cat_name)
            if created:
                self.stdout.write(f"Catégorie créée : {cat_name}")
            
            for prob_name in probs:
                prob, p_created = Probleme.objects.get_or_create(
                    categorie=category,
                    libelle=prob_name,
                    defaults={'actif': True}
                )
                if p_created:
                    self.stdout.write(f"  Problème créé : {prob_name}")

        # 3. Création des Priorités
        priorities_data = [
            ('Faible', 1),
            ('Moyenne', 2),
            ('Haute', 3),
            ('Urgente', 4)
        ]
        for name, level in priorities_data:
            prio, created = Priorite.objects.get_or_create(libelle=name, defaults={'niveau': level})
            if created:
                self.stdout.write(f"Priorité créée : {name} (Niveau {level})")

        # 4. Création des Statuts
        status_data = ['Nouveau', 'Assigné', 'En cours', 'Résolu', 'Clôturé']
        for s_name in status_data:
            stat, created = StatutTicket.objects.get_or_create(libelle=s_name)
            if created:
                self.stdout.write(f"Statut créé : {s_name}")

        # 5. Création des Utilisateurs par défaut
        users_to_create = [
            ('admin', 'admin@itsm.com', 'Admin', True, True),
            ('tech1', 'tech1@itsm.com', 'Technicien', False, True),
            ('tech2', 'tech2@itsm.com', 'Technicien', False, True),
            ('client1', 'client1@itsm.com', 'Client', False, False),
            ('client2', 'client2@itsm.com', 'Client', False, False),
        ]

        for username, email, role_name, is_super, is_staff in users_to_create:
            if not Utilisateur.objects.filter(username=username).exists():
                user = Utilisateur.objects.create_user(
                    username=username,
                    email=email,
                    password='password123',
                    role=roles[role_name],
                    is_superuser=is_super,
                    is_staff=is_staff or is_super
                )
                self.stdout.write(f"Utilisateur créé : {username} (Rôle: {role_name}, password: password123)")
            else:
                self.stdout.write(f"Utilisateur existant : {username}")

        self.stdout.write(self.style.SUCCESS("Initialisation réussie !"))
