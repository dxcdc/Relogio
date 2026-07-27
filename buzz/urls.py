from django.urls import path
from . import views

urlpatterns = [
    
    path('', views.buzz_feed, name='buzz_feed'),
    path('post/', views.create_post, name='create_post'),
    path('share/<int:pk>/like/', views.like_share, name='like_share'),
    path('share/<int:share_pk>/comment/', views.add_comment, name='add_comment'),
    path('share/<int:share_pk>/delete/', views.delete_post, name='delete_post'),

    
    path('novidades/', views.changelog_list, name='changelog_list'),
    path('novidades/nova/', views.changelog_create, name='changelog_create'),
    path('novidades/<int:pk>/deletar/', views.changelog_delete, name='changelog_delete'),
    path('bugs/', views.bug_list, name='bug_list'),
    path('bugs/novo/', views.bug_create, name='bug_create'),
    path('bugs/<int:pk>/', views.bug_detail, name='bug_detail'),
    path('bugs/<int:pk>/comentar/', views.bug_comment_add, name='bug_comment_add'),
    path('bugs/<int:pk>/assumir/', views.bug_claim, name='bug_claim'),
    path('bugs/<int:pk>/status/', views.bug_status_update, name='bug_status_update'),

    # Painel de denúncias — Apple Guideline 1.2
    path('denuncias/', views.content_reports, name='content_reports'),
    path('denuncias/<int:pk>/atualizar/', views.update_content_report, name='update_content_report'),

    # Central de Suporte unificada (Bugs + Denúncias)
    path('central-suporte/', views.central_suporte, name='central_suporte'),
    path('netgram-moderation/', views.netgram_user_moderation, name='netgram_user_moderation'),
]
