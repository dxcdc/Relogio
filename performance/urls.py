from django.urls import path
from . import views

urlpatterns = [
    path('reviews/', views.review_list, name='review_list'),
    path('reviews/add/', views.review_create, name='review_create'),
    path('reviews/<int:pk>/', views.review_detail, name='review_detail'),
    path('reviews/<int:pk>/edit/', views.review_edit, name='review_edit'),
    path('reviews/<int:pk>/delete/', views.review_delete, name='review_delete'),
    path('kpis/', views.kpi_list, name='kpi_list'),
    path('kpis/add/', views.kpi_create, name='kpi_create'),
    path('kpis/<int:pk>/edit/', views.kpi_edit, name='kpi_edit'),
    path('kpis/<int:pk>/delete/', views.kpi_delete, name='kpi_delete'),
    path('trackers/', views.tracker_list, name='tracker_list'),
    path('trackers/add/', views.tracker_create, name='tracker_create'),
    path('trackers/<int:pk>/', views.tracker_detail, name='tracker_detail'),
    path('trackers/<int:pk>/delete/', views.tracker_delete, name='tracker_delete'),
    
    
    path('surveys/', views.survey_list, name='survey_list'),
    path('surveys/rankings/', views.survey_ranking_list, name='survey_ranking_list'),
    path('surveys/create/', views.survey_create, name='survey_create'),
    path('surveys/<int:pk>/edit/', views.survey_edit, name='survey_edit'),
    path('surveys/<int:pk>/delete/', views.survey_delete, name='survey_delete'),
    path('surveys/<int:pk>/results/', views.survey_results, name='survey_results'),
    path('surveys/<int:pk>/take/', views.survey_take, name='survey_take'),
]
