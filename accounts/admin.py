from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'escola_nome', 'plano', 'ativo', 'data_criacao')
    list_filter = ('plano', 'ativo', 'data_criacao')
    search_fields = ('user__username', 'escola_nome')
    readonly_fields = ('data_criacao',)
