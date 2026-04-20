from django.urls import path
from . import views

urlpatterns = [
    path('alunos/', views.alunos_list, name='alunos_list'),
    path('alunos/novo/', views.aluno_create, name='aluno_create'),
    path('alunos/<int:pk>/', views.aluno_detail, name='aluno_detail'),
    path('alunos/<int:pk>/editar/', views.aluno_update, name='aluno_update'),
    path('alunos/<int:pk>/deletar/', views.aluno_delete, name='aluno_delete'),
    path('internal/import-alunos/', views.CadastroMassaAlunosView.as_view()),
]
