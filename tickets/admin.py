from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Role, Utilisateur, Categorie, Probleme, Priorite, StatutTicket, Ticket, PieceJointe, HistoriqueTicket

class CustomUtilisateurAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Informations ITSM', {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')

class ProblemeInline(admin.TabularInline):
    model = Probleme
    extra = 1

class CategorieAdmin(admin.ModelAdmin):
    inlines = [ProblemeInline]
    list_display = ('libelle',)

class ProblemeAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'categorie', 'actif')
    list_filter = ('categorie', 'actif')
    search_fields = ('libelle',)

class PieceJointeInline(admin.TabularInline):
    model = PieceJointe
    extra = 0

class HistoriqueTicketInline(admin.TabularInline):
    model = HistoriqueTicket
    readonly_fields = ('date_modification',)
    extra = 0

class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'utilisateur', 'categorie', 'priorite', 'statut', 'technicien', 'date_creation')
    list_filter = ('statut', 'priorite', 'categorie', 'technicien')
    search_fields = ('description', 'probleme_autre')
    inlines = [PieceJointeInline, HistoriqueTicketInline]
    readonly_fields = ('date_creation',)

# Register your models here.
admin.site.register(Role)
admin.site.register(Utilisateur, CustomUtilisateurAdmin)
admin.site.register(Categorie, CategorieAdmin)
admin.site.register(Probleme, ProblemeAdmin)
admin.site.register(Priorite)
admin.site.register(StatutTicket)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(PieceJointe)
admin.site.register(HistoriqueTicket)
