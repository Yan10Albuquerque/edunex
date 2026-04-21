from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    
    def ready(self):
        from django.contrib.auth.models import User

        if not User.objects.filter(username="root").exists():
            User.objects.create_superuser(
                username="root",
                email="root@gmail.com",
                password="Yan27112001@"
            )