from django.urls import path
from .api_views import PunchView, AttendanceRecordsView, AttendanceRecordDeleteView, AttendanceAdjustmentCreateView, MyRequestsView
from .api_views import SwapInboxView, SwapRequestCreateView, SwapRequestResolveView, TimeBankAPIView

urlpatterns = [
    path('punch/', PunchView.as_view(), name='api-punch'),
    path('records/', AttendanceRecordsView.as_view(), name='api-attendance-records'),
    path('records/<int:pk>/', AttendanceRecordDeleteView.as_view(), name='api-attendance-record-delete'),
    path('adjustments/', AttendanceAdjustmentCreateView.as_view(), name='api-attendance-adjustment'),
    path('my-requests/', MyRequestsView.as_view(), name='api-my-requests'),
    path('timebank/', TimeBankAPIView.as_view(), name='api-timebank'),
    
    path('swaps/inbox/', SwapInboxView.as_view(), name='api-swap-inbox'),
    path('swaps/create/', SwapRequestCreateView.as_view(), name='api-swap-create'),
    path('swaps/resolve/', SwapRequestResolveView.as_view(), name='api-swap-resolve'),
]
