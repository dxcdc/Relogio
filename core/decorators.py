from django.core.exceptions import PermissionDenied
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def require_module(module_name):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
                
            
            
            
            from core.models import RoleModuleAccess
            try:
                acc = RoleModuleAccess.objects.get(role=request.user.role)
                has_access = getattr(acc, module_name, True)
            except Exception:
                has_access = True
                
            if not has_access:
                messages.error(request, 'Você não possui permissão para acessar o módulo: ' + module_name.capitalize())
                return redirect('dashboard')
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
