from django.urls import path
from .api_views import PendingSurveyListAPIView, SurveyDetailAPIView

urlpatterns = [
    path('surveys/pending/', PendingSurveyListAPIView.as_view(), name='api_surveys_pending'),
    path('surveys/<int:pk>/', SurveyDetailAPIView.as_view(), name='api_survey_detail'),
]
