from django.urls import path
from .api_views import (
    ChangelogListAPIView, MyBugReportsAPIView, CreateBugReportAPIView, BugReportDetailAPIView,
    BuzzFeedAPIView, CreateBuzzPostAPIView, ToggleBuzzLikeAPIView, AddBuzzCommentAPIView,
    ReportContentAPIView, BlockUserAPIView,
)

urlpatterns = [
    path('changelogs/', ChangelogListAPIView.as_view(), name='api-changelogs'),
    path('my-reports/', MyBugReportsAPIView.as_view(), name='api-my-reports'),
    path('report/', CreateBugReportAPIView.as_view(), name='api-create-report'),
    path('report/<int:pk>/', BugReportDetailAPIView.as_view(), name='api-report-detail'),
    path('feed/', BuzzFeedAPIView.as_view(), name='api-buzz-feed'),
    path('feed/post/', CreateBuzzPostAPIView.as_view(), name='api-buzz-post'),
    path('feed/<int:pk>/like/', ToggleBuzzLikeAPIView.as_view(), name='api-buzz-like'),
    path('feed/<int:pk>/comment/', AddBuzzCommentAPIView.as_view(), name='api-buzz-comment'),
    # Denúncia de conteúdo — Apple Guideline 1.2
    path('report-content/', ReportContentAPIView.as_view(), name='api-report-content'),
    # Bloqueio de usuário — Apple Guideline 1.2
    path('block-user/', BlockUserAPIView.as_view(), name='api-block-user'),
]
