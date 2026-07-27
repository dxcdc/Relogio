from django.apps import AppConfig
from django.db.models.signals import post_migrate


def populate_default_roles(sender, **kwargs):
    from core.models import RoleModuleAccess, OrangeUser
    import os
    
    # 1. Cria os perfis e acessos padrões
    try:
        for role_code, role_name in OrangeUser.ROLE_CHOICES:
            RoleModuleAccess.objects.get_or_create(role=role_code)
    except Exception:
        pass

    # 2. Cria o Superusuário Administrador padrão de forma segura (valores do .env)
    try:
        username = os.environ.get('ADMIN_USERNAME')
        email = os.environ.get('ADMIN_EMAIL')
        password = os.environ.get('ADMIN_PASSWORD')
        
        if username and email and password:
            if not OrangeUser.objects.filter(username=username).exists():
                OrangeUser.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password,
                    role=OrangeUser.ROLE_ADMIN
                )
                print(f"\n[CDC] Administrador '{username}' criado automaticamente com sucesso!")
    except Exception as e:
        print(f"\n[CDC] Erro ao criar administrador automático: {e}")


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        post_migrate.connect(populate_default_roles, sender=self)

