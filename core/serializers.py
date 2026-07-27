from rest_framework import serializers
from .models import OrangeUser

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    employee_id = serializers.SerializerMethodField()
    is_supervisor = serializers.SerializerMethodField()
    picture_url = serializers.SerializerMethodField()
    can_post_netgram = serializers.SerializerMethodField()
    allow_shift_swaps = serializers.SerializerMethodField()
    
    class Meta:
        model = OrangeUser
        fields = ['id', 'username', 'email', 'role', 'full_name', 'employee_id', 'is_supervisor', 'picture_url', 'can_post_netgram', 'allow_shift_swaps']
        
    def get_can_post_netgram(self, obj):
        from core.models import RoleModuleAccess
        if obj.role:
            acc = RoleModuleAccess.objects.filter(role=obj.role).first()
            if acc:
                return acc.netgram_post
        return True
        
    def get_allow_shift_swaps(self, obj):
        try:
            if hasattr(obj, 'employee') and obj.employee and hasattr(obj.employee, 'sub_division') and obj.employee.sub_division:
                return obj.employee.sub_division.allow_shift_swaps
        except Exception:
            pass
        return False
        
    def get_full_name(self, obj):
        if hasattr(obj, 'employee') and obj.employee:
            return obj.employee.full_name
        return obj.get_full_name() or obj.username
        
    def get_employee_id(self, obj):
        if hasattr(obj, 'employee') and obj.employee:
            return obj.employee.pk
        return None
        
    def get_is_supervisor(self, obj):
        return obj.is_supervisor()

    def get_picture_url(self, obj):
        try:
            if hasattr(obj, 'employee') and obj.employee and hasattr(obj.employee, 'picture') and obj.employee.picture and obj.employee.picture.picture:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.employee.picture.picture.url)
                return obj.employee.picture.picture.url
        except Exception:
            pass
        return None
