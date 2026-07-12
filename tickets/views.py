from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import models
from django.db.models import Count
from django.utils import timezone
from .models import (
    Role, Categorie, Probleme, Priorite, StatutTicket, SourceTicket,
    Ticket, PieceJointe, HistoriqueTicket, Utilisateur
)

def redirect_by_role(user):
    if user.is_admin or user.is_technicien:
        return redirect('admin_dashboard')
    else:
        return redirect('client_dashboard')

def login_view(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)
    
    error_message = None
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            return redirect_by_role(user)
        else:
            error_message = "Identifiants invalides."
            
    return render(request, 'tickets/login.html', {'error_message': error_message})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_redirect(request):
    return redirect_by_role(request.user)

# ==================== PORTAIL CLIENT ====================

@login_required
def client_dashboard(request):
    if not request.user.is_client:
        return redirect('admin_dashboard')
    
    categories = Categorie.objects.all()
    return render(request, 'tickets/client/dashboard.html', {
        'categories': categories
    })

@login_required
def client_tickets(request):
    if not request.user.is_client:
        return redirect('admin_dashboard')
        
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search')
    
    base_tickets = Ticket.objects.filter(utilisateur=request.user)

    # Stats on all client tickets (independent of active filters)
    stats = base_tickets.aggregate(
        total=Count('id'),
        nouveau=Count('id', filter=models.Q(statut__libelle='Nouveau')),
        en_cours=Count('id', filter=models.Q(statut__libelle='En cours') | models.Q(statut__libelle='Assigné')),
        resolu=Count('id', filter=models.Q(statut__libelle='Résolu') | models.Q(statut__libelle='Clôturé'))
    )

    tickets = base_tickets.order_by('-date_creation')

    if status_filter:
        tickets = tickets.filter(statut__libelle=status_filter)
    if search_query:
        tickets = tickets.filter(
            models.Q(description__icontains=search_query) |
            models.Q(probleme__libelle__icontains=search_query) |
            models.Q(probleme_autre__icontains=search_query)
        )
    
    return render(request, 'tickets/client/tickets_list.html', {
        'tickets': tickets,
        'stats': stats,
        'selected_status': status_filter,
        'search_query': search_query
    })

@login_required
def creer_ticket(request):
    if not request.user.is_client:
        return redirect('admin_dashboard')

    priorities = Priorite.objects.all().order_by('niveau')

    if request.method == 'POST':
        categorie_id = request.POST.get('categorie')
        probleme_id = request.POST.get('probleme')
        probleme_autre = request.POST.get('probleme_autre')
        priorite_id = request.POST.get('priorite')
        description = request.POST.get('description', '')

        categorie = get_object_or_404(Categorie, id=categorie_id)
        priorite = get_object_or_404(Priorite, id=priorite_id)
        statut_nouveau = get_object_or_404(StatutTicket, libelle='Nouveau')
        source_portail = SourceTicket.objects.filter(libelle='Portail Web').first()

        probleme = None
        if probleme_id and probleme_id != 'autre':
            probleme = get_object_or_404(Probleme, id=probleme_id)

        ticket = Ticket.objects.create(
            utilisateur=request.user,
            categorie=categorie,
            probleme=probleme,
            probleme_autre=probleme_autre if not probleme else None,
            priorite=priorite,
            statut=statut_nouveau,
            source=source_portail,
            description=description
        )

        HistoriqueTicket.objects.create(
            ticket=ticket,
            ancien_statut=None,
            nouveau_statut=statut_nouveau,
            modifie_par=request.user,
            commentaire="Création initiale du ticket par le client."
        )

        files = request.FILES.getlist('fichiers')
        for f in files:
            PieceJointe.objects.create(
                ticket=ticket,
                fichier=f,
                nom_original=f.name,
                uploaded_by=request.user
            )

        return redirect('client_tickets')

    categorie_id = request.GET.get('categorie_id')
    if not categorie_id:
        return redirect('client_dashboard')

    selected_categorie = get_object_or_404(Categorie, id=categorie_id)

    return render(request, 'tickets/client/creer_ticket.html', {
        'selected_categorie': selected_categorie,
        'priorities': priorities,
    })

@login_required
def detail_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Security check: Client can only view their own tickets
    if request.user.is_client and ticket.utilisateur != request.user:
        return redirect('client_dashboard')
        
    # Handle user adding a comment
    if request.method == 'POST':
        commentaire = request.POST.get('commentaire')
        if commentaire:
            # When client or tech adds a message, we create an history event with the same status
            HistoriqueTicket.objects.create(
                ticket=ticket,
                ancien_statut=ticket.statut,
                nouveau_statut=ticket.statut,
                modifie_par=request.user,
                commentaire=commentaire
            )
            
            # Handle attachment upload from the ticket detail chat/thread
            files = request.FILES.getlist('fichiers')
            for f in files:
                PieceJointe.objects.create(
                    ticket=ticket,
                    fichier=f,
                    nom_original=f.name,
                    uploaded_by=request.user
                )
                
            return redirect('detail_ticket', ticket_id=ticket.id)
            
    historiques = ticket.historiques.all().order_by('date_modification')
    pieces_jointes = ticket.pieces_jointes.all()
    
    return render(request, 'tickets/client/detail_ticket.html', {
        'ticket': ticket,
        'historiques': historiques,
        'pieces_jointes': pieces_jointes
    })

@login_required
def api_get_problemes(request):
    categorie_id = request.GET.get('categorie_id')
    if not categorie_id:
        return JsonResponse({'problemes': []})
        
    problemes = Probleme.objects.filter(categorie_id=categorie_id, actif=True).values('id', 'libelle')
    return JsonResponse({'problemes': list(problemes)})


# ==================== PORTAIL ADMIN / TECHNICIEN ====================

@login_required
def admin_dashboard(request):
    if not (request.user.is_admin or request.user.is_technicien):
        return redirect('client_dashboard')
        
    # 1. Tickets par statut
    tickets_par_statut = Ticket.objects.values('statut__libelle').annotate(count=Count('id'))
    status_counts = {item['statut__libelle']: item['count'] for item in tickets_par_statut}
    # Enforce standard order
    status_order = ['Nouveau', 'Assigné', 'En cours', 'Résolu', 'Clôturé']
    status_chart_data = {s: status_counts.get(s, 0) for s in status_order}
    
    # 2. Charge de l'équipe de support (tickets non résolus/clôturés affectés aux techniciens)
    tech_role = Role.objects.get(libelle='Technicien')
    techniciens = Utilisateur.objects.filter(role=tech_role, is_active=True)
    
    workload_data = []
    for tech in techniciens:
        assigned_count = Ticket.objects.filter(
            technicien=tech
        ).exclude(statut__libelle__in=['Résolu', 'Clôturé']).count()
        workload_data.append({
            'username': tech.username,
            'count': assigned_count
        })
        
    # 3. Problèmes récurrents (Top 5 des problèmes prédéfinis les plus signalés)
    problemes_recurrents = Ticket.objects.filter(probleme__isnull=False)\
        .values('categorie__libelle', 'probleme__libelle')\
        .annotate(count=Count('id'))\
        .order_by('-count')[:5]
        
    # Add count for custom problems if any
    custom_probs_count = Ticket.objects.filter(probleme__isnull=True).count()
    
    # Global stats
    total_tickets = Ticket.objects.count()
    nouveaux_tickets = Ticket.objects.filter(statut__libelle='Nouveau').count()
    resolus_tickets = Ticket.objects.filter(statut__libelle='Résolu').count()
    
    return render(request, 'tickets/admin/dashboard_analytics.html', {
        'status_chart_data': status_chart_data,
        'workload_data': workload_data,
        'problemes_recurrents': problemes_recurrents,
        'custom_probs_count': custom_probs_count,
        'total_tickets': total_tickets,
        'nouveaux_tickets': nouveaux_tickets,
        'resolus_tickets': resolus_tickets
    })

@login_required
def admin_liste_tickets(request):
    if not (request.user.is_admin or request.user.is_technicien):
        return redirect('client_dashboard')
        
    statut_filter = request.GET.get('statut')
    categorie_filter = request.GET.get('categorie')
    technicien_filter = request.GET.get('technicien')
    priorite_filter = request.GET.get('priorite')
    
    tickets = Ticket.objects.all().order_by('-date_creation')
    
    if statut_filter:
        tickets = tickets.filter(statut__id=statut_filter)
    if categorie_filter:
        tickets = tickets.filter(categorie__id=categorie_filter)
    if technicien_filter:
        if technicien_filter == 'none':
            tickets = tickets.filter(technicien__isnull=True)
        else:
            tickets = tickets.filter(technicien__id=technicien_filter)
    if priorite_filter:
        tickets = tickets.filter(priorite__id=priorite_filter)
        
    statuts = StatutTicket.objects.all()
    categories = Categorie.objects.all()
    priorites = Priorite.objects.all().order_by('niveau')
    
    tech_role = Role.objects.get(libelle='Technicien')
    techniciens = Utilisateur.objects.filter(role=tech_role)
    
    return render(request, 'tickets/admin/liste_tickets.html', {
        'tickets': tickets,
        'statuts': statuts,
        'categories': categories,
        'priorites': priorites,
        'techniciens': techniciens,
        'selected_statut': int(statut_filter) if statut_filter else None,
        'selected_categorie': int(categorie_filter) if categorie_filter else None,
        'selected_technicien': technicien_filter, # could be string 'none' or ID
        'selected_priorite': int(priorite_filter) if priorite_filter else None,
    })

@login_required
def admin_detail_ticket(request, ticket_id):
    if not (request.user.is_admin or request.user.is_technicien):
        return redirect('client_dashboard')
        
    ticket = get_object_or_404(Ticket, id=ticket_id)
    statuts = StatutTicket.objects.all()
    sources = SourceTicket.objects.filter(actif=True).order_by('libelle')
    
    tech_role = Role.objects.get(libelle='Technicien')
    techniciens = Utilisateur.objects.filter(role=tech_role, is_active=True)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        commentaire = request.POST.get('commentaire', '')
        
        # Action : Assigner un technicien
        if action == 'assigner':
            tech_id = request.POST.get('technicien')
            nouveau_technicien = get_object_or_404(Utilisateur, id=tech_id) if tech_id else None
            
            ancien_statut = ticket.statut
            statut_assigne = get_object_or_404(StatutTicket, libelle='Assigné')
            
            comment_log = f"Ticket assigné à {nouveau_technicien.username}."
            if commentaire:
                comment_log += f" Note: {commentaire}"
                
            ticket.technicien = nouveau_technicien
            ticket.statut = statut_assigne
            ticket.date_assignation = timezone.now()
            ticket.save()
            
            HistoriqueTicket.objects.create(
                ticket=ticket,
                ancien_statut=ancien_statut,
                nouveau_statut=statut_assigne,
                modifie_par=request.user,
                commentaire=comment_log
            )
            
        # Action : Changer le statut
        elif action == 'changer_statut':
            statut_id = request.POST.get('statut')
            nouveau_statut = get_object_or_404(StatutTicket, id=statut_id)
            
            ancien_statut = ticket.statut
            ticket.statut = nouveau_statut
            
            # Log specific timestamps
            if nouveau_statut.libelle == 'En cours' and not ticket.date_assignation:
                ticket.date_assignation = timezone.now()
            elif nouveau_statut.libelle == 'Résolu':
                ticket.date_resolution = timezone.now()
            elif nouveau_statut.libelle == 'Clôturé':
                ticket.date_cloture = timezone.now()
                
            ticket.save()
            
            comment_log = f"Statut modifié : {ancien_statut.libelle} -> {nouveau_statut.libelle}."
            if commentaire:
                comment_log += f" Note: {commentaire}"
                
            HistoriqueTicket.objects.create(
                ticket=ticket,
                ancien_statut=ancien_statut,
                nouveau_statut=nouveau_statut,
                modifie_par=request.user,
                commentaire=comment_log
            )
            
        # Action : Modifier la source du ticket
        elif action == 'modifier_source':
            source_id = request.POST.get('source')
            nouvelle_source = get_object_or_404(SourceTicket, id=source_id) if source_id else None
            
            ancienne_source = ticket.source
            ticket.source = nouvelle_source
            ticket.save()
            
            ancienne_source_libelle = ancienne_source.libelle if ancienne_source else "Non définie"
            nouvelle_source_libelle = nouvelle_source.libelle if nouvelle_source else "Non définie"
            
            comment_log = f"Source du ticket modifiée : {ancienne_source_libelle} → {nouvelle_source_libelle}."
            if commentaire:
                comment_log += f" Note: {commentaire}"
                
            HistoriqueTicket.objects.create(
                ticket=ticket,
                ancien_statut=ticket.statut,
                nouveau_statut=ticket.statut,
                modifie_par=request.user,
                commentaire=comment_log
            )
        
        # Action : Ajouter un simple message/commentaire
        elif action == 'ajouter_commentaire':
            if commentaire:
                HistoriqueTicket.objects.create(
                    ticket=ticket,
                    ancien_statut=ticket.statut,
                    nouveau_statut=ticket.statut,
                    modifie_par=request.user,
                    commentaire=commentaire
                )
                
                # Upload files from here too
                files = request.FILES.getlist('fichiers')
                for f in files:
                    PieceJointe.objects.create(
                        ticket=ticket,
                        fichier=f,
                        nom_original=f.name,
                        uploaded_by=request.user
                    )
                    
        return redirect('admin_detail_ticket', ticket_id=ticket.id)
        
    historiques = ticket.historiques.all().order_by('date_modification')
    pieces_jointes = ticket.pieces_jointes.all()
    
    return render(request, 'tickets/admin/detail_ticket.html', {
        'ticket': ticket,
        'statuts': statuts,
        'sources': sources,
        'techniciens': techniciens,
        'historiques': historiques,
        'pieces_jointes': pieces_jointes
    })

# ==================== PROFIL UTILISATEUR ====================

@login_required
def user_profile(request):
    user = request.user
    
    if request.method == 'POST':
        # Mise à jour du profil utilisateur
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        return redirect('user_profile')
    
    return render(request, 'tickets/profile.html', {
        'user': user
    })
