from django.contrib import admin
from .models import Aluno


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'responsavel', 'telefone', 'usuario', 'data_criacao')
    list_filter = ('usuario', 'data_criacao')
    search_fields = ('nome', 'responsavel', 'telefone')
    readonly_fields = ('data_criacao', 'data_atualizacao')
    fieldsets = (
        ('Informacoes Basicas', {
            'fields': ('usuario', 'nome', 'responsavel')
        }),
        ('Contato', {
            'fields': ('telefone', 'email')
        }),
        ('Timestamps', {
            'fields': ('data_criacao', 'data_atualizacao'),
            'classes': ('collapse',)
        }),
    )
