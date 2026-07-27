from django.urls import path
from . import api_views

urlpatterns = [
    path('calendar/', api_views.LeaveCalendarAPIView.as_view(), name='api_leave_calendar'),
    path('types/', api_views.LeaveTypeAPIView.as_view(), name='api_leave_types'),
    path('add/', api_views.LeaveRequestCreateAPIView.as_view(), name='api_leave_add'),
]
