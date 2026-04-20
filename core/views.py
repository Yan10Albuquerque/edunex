from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Aluno
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from django.contrib.auth.models import User
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
    if request.method == 'POST':
        nome = request.POST.get('nome')
        responsavel = request.POST.get('responsavel')
        telefone = request.POST.get('telefone')
        email = request.POST.get('email', '')
        
        aluno = Aluno.objects.create(
            usuario=request.user,
            nome=nome,
            responsavel=responsavel,
            telefone=telefone,
            email=email
        )
        
        messages.success(request, f'Aluno {nome} cadastrado com sucesso!')
        return redirect('alunos_list')
    
    return render(request, 'core/aluno_form.html')


@login_required(login_url='login')
@plano_profissional_required
def aluno_update(request, pk):
    """
    Editar aluno
    """
    aluno = get_object_or_404(Aluno, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        aluno.nome = request.POST.get('nome', aluno.nome)
        aluno.responsavel = request.POST.get('responsavel', aluno.responsavel)
        aluno.telefone = request.POST.get('telefone', aluno.telefone)
        aluno.email = request.POST.get('email', aluno.email)
        aluno.save()
        
        messages.success(request, f'Aluno {aluno.nome} atualizado com sucesso!')
        return redirect('alunos_list')
    
    context = {
        'aluno': aluno,
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
    # 🔥 Isso ativa a tela no navegador
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    def get(self, request):
        return Response({"message": "Use POST para enviar os dados"})

    def post(self, request):
        serializer = AlunoBulkSerializer(data=request.data, many=True)

        if serializer.is_valid():
            alunos = [
                Aluno(**item)
                for item in serializer.validated_data
            ]

            Aluno.objects.bulk_create(alunos)

            return Response(
                {"message": f"{len(alunos)} alunos cadastrados com sucesso"},
                status=201
            )

        return Response(serializer.errors, status=400)