from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_redirect, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.user_profile, name='user_profile'),
    
    # Client Portal
    path('client/dashboard/', views.client_dashboard, name='client_dashboard'),
    path('client/tickets/', views.client_tickets, name='client_tickets'),
    path('client/ticket/nouveau/', views.creer_ticket, name='creer_ticket'),
    path('client/ticket/<int:ticket_id>/', views.detail_ticket, name='detail_ticket'),
    
    # AJAX API
    path('api/problemes/', views.api_get_problemes, name='api_get_problemes'),
    
    # Admin/Tech Portal
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/tickets/', views.admin_liste_tickets, name='admin_liste_tickets'),
    path('admin/ticket/nouveau/', views.admin_creer_ticket, name='admin_creer_ticket'),
    path('admin/ticket/<int:ticket_id>/', views.admin_detail_ticket, name='admin_detail_ticket'),
]
