from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('mensalidades/nova/', views.mensalidade_create, name='mensalidade_create'),
    path('mensalidades/<int:pk>/editar/', views.mensalidade_update, name='mensalidade_update'),
    path('mensalidades/<int:pk>/deletar/', views.mensalidade_delete, name='mensalidade_delete'),
    path('mensalidades/<int:pk>/pagar/', views.mensalidade_pagar, name='mensalidade_pagar'),
    path('mensalidades/<int:pk>/cobrar/', views.mensalidade_cobrar, name='mensalidade_cobrar'),
    path('internal/import-mensalidades/', views.CadastroMassaMensalidadeView.as_view(), name='import_mensalidades'),
]
