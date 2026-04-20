from django.contrib import admin
from .models import Mensalidade


@admin.register(Mensalidade)
class MensalidadeAdmin(admin.ModelAdmin):
    list_display = ('id', 'aluno', 'valor', 'data_vencimento', 'status', 'recorrente', 'usuario')
    list_filter = ('status', 'recorrente', 'data_vencimento', 'usuario')
    search_fields = ('aluno__nome', 'usuario__username')
    readonly_fields = ('data_criacao', 'data_atualizacao', 'mensalidade_anterior')
    actions = ['marcar_como_pago']
    fieldsets = (
        ('Informacoes da Mensalidade', {
            'fields': ('usuario', 'aluno', 'valor')
        }),
        ('Datas', {
            'fields': ('data_vencimento', 'data_pagamento')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Recorrencia', {
            'fields': ('recorrente', 'data_fim_recorrencia', 'mensalidade_anterior'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('data_criacao', 'data_atualizacao'),
            'classes': ('collapse',)
        }),
    )
    
    def marcar_como_pago(self, request, queryset):
        for mensalidade in queryset:
            mensalidade.marcar_como_pago()
        self.message_user(request, f'{queryset.count()} mensalidade(s) marcada(s) como paga(s).')
    
    marcar_como_pago.short_description = 'Marcar como pago'
