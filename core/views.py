from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .forms import AlunoForm
from .models import Aluno
from .utils import exibir_erros_formulario
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from .serializers import AlunoBulkSerializer
from accounts.decorators import plano_profissional_required


@login_required(login_url='login')
def alunos_list(request):
    """
    Listagem de alunos do usuario logado
    """
    alunos = Aluno.objects.filter(usuario=request.user).order_by('nome')
    
    # Filtro por busca
    busca = request.GET.get('busca', '')
    if busca:
        alunos = alunos.filter(
            Q(nome__icontains=busca) | 
            Q(responsavel__icontains=busca) |
            Q(telefone__icontains=busca)
        )
    
    context = {
        'alunos': alunos,
        'busca': busca,
    }
    return render(request, 'core/alunos_list.html', context)


@login_required(login_url='login')
@plano_profissional_required
def aluno_create(request):
    """
    Criar novo aluno
    """
    form = AlunoForm(request.POST or None, instance=Aluno(usuario=request.user))

    if request.method == 'POST':
        if form.is_valid():
            aluno = form.save()
            messages.success(request, f'Aluno {aluno.nome} cadastrado com sucesso!')
            return redirect('alunos_list')
        exibir_erros_formulario(request, form)

    return render(request, 'core/aluno_form.html', {'aluno': form.instance})


@login_required(login_url='login')
@plano_profissional_required
def aluno_update(request, pk):
    """
    Editar aluno
    """
    aluno = get_object_or_404(Aluno, pk=pk, usuario=request.user)
    form = AlunoForm(request.POST or None, instance=aluno)

    if request.method == 'POST':
        if form.is_valid():
            aluno = form.save()
            messages.success(request, f'Aluno {aluno.nome} atualizado com sucesso!')
            return redirect('alunos_list')
        exibir_erros_formulario(request, form)

    context = {
        'aluno': form.instance,
        'edit': True,
    }
    return render(request, 'core/aluno_form.html', context)


@login_required(login_url='login')
@plano_profissional_required
def aluno_delete(request, pk):
    """
    Deletar aluno
    """
    aluno = get_object_or_404(Aluno, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        nome = aluno.nome
        aluno.delete()
        messages.success(request, f'Aluno {nome} deletado com sucesso!')
        return redirect('alunos_list')
    
    context = {
        'aluno': aluno,
    }
    return render(request, 'core/aluno_confirm_delete.html', context)


@login_required(login_url='login')
@plano_profissional_required
def aluno_detail(request, pk):
    """
    Detalhes do aluno e suas mensalidades
    """
    aluno = get_object_or_404(Aluno, pk=pk, usuario=request.user)
    mensalidades = aluno.mensalidades.all().order_by('-data_vencimento')
    
    context = {
        'aluno': aluno,
        'mensalidades': mensalidades,
    }
    return render(request, 'core/aluno_detail.html', context)


######### API ALUNOS #########

class CadastroMassaAlunosView(APIView):
    """
    Importacao em massa de alunos (uso interno, apenas equipe/staff).
    """
    permission_classes = [IsAdminUser]
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    def get(self, request):
        return Response({"message": "Use POST para enviar os dados"})

    def post(self, request):
        if not isinstance(request.data, list):
            return Response({"error": "Envie uma lista de alunos"}, status=400)

        serializer = AlunoBulkSerializer(data=request.data, many=True)

        if serializer.is_valid():
            alunos = [
                Aluno(**item)
                for item in serializer.validated_data
            ]

            with transaction.atomic():
                Aluno.objects.bulk_create(alunos)

            return Response(
                {"message": f"{len(alunos)} alunos cadastrados com sucesso"},
                status=201
            )

        return Response(serializer.errors, status=400)