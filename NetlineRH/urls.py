from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('pim/', include('pim.urls')),
    path('admin-panel/', include('admin_app.urls')),
    path('leave/', include('leave.urls')),
    path('attendance/', include('attendance.urls')),
    path('time/', include('time_tracking.urls')),
    path('performance/', include('performance.urls')),
    path('buzz/', include('buzz.urls')),
    path('claim/', include('claim.urls')),
    path('send/', include('emails.urls')),
    path('payroll/', include('payroll.urls')),
    path('agenda/', include('agenda.urls')),
    path('recruitment/', include('recruitment.urls')),
    
    path('api/v1/auth/', include('core.api_urls')),
    path('api/v1/pim/', include('pim.api_urls')),
    path('api/v1/attendance/', include('attendance.api_urls')),
    path('api/v1/leave/', include('leave.api_urls')),
    path('api/v1/buzz/', include('buzz.api_urls')),
    path('api/v1/payroll/', include('payroll.api_urls')),
    path('api/v1/performance/', include('performance.api_urls')),
    
    # Swagger API Schema & UI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
