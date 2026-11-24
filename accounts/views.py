from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from core.utils import exibir_erros_formulario

from .demo import criar_visitante, is_visitante, limpar_visitantes_expirados
from .forms import PerfilForm, RegistroForm
from .models import UserProfile


def register(request):
    """
    View para registro de novo usuario (escola)
    """
    if request.user.is_authenticated and not is_visitante(request.user):
        return redirect('dashboard')

    form = RegistroForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            dados = form.cleaned_data
            with transaction.atomic():
                user = User.objects.create_user(
                    username=dados['username'],
                    email=dados['email'],
                    password=dados['password'],
                    first_name=dados['escola_nome'][:150],
                )
                UserProfile.objects.create(
                    user=user,
                    escola_nome=dados['escola_nome'],
                    telefone=dados['telefone'],
                )

            messages.success(request, 'Registro realizado com sucesso! Faca login.')
            return redirect('login')
        exibir_erros_formulario(request, form)

    return render(request, 'accounts/register.html', {'dados': request.POST})


def login_view(request):
    if request.user.is_authenticated and not is_visitante(request.user):
        return redirect('dashboard')

    proxima = request.POST.get('next') or request.GET.get('next', '')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if is_visitante(request.user):
                _encerrar_visitante(request)
            login(request, user)
            messages.success(request, f'Bem-vindo, {user.first_name or user.username}!')
            if url_has_allowed_host_and_scheme(
                proxima,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(proxima)
            return redirect('dashboard')

        messages.error(request, 'Usuario ou senha invalidos.')

    return render(request, 'accounts/login.html', {'next': proxima})


@require_POST
def visitante_entrar(request):
    """
    Modo visitante: cria uma conta temporaria com dados ficticios e entra nela.
    """
    if request.user.is_authenticated and not is_visitante(request.user):
        return redirect('dashboard')

    if is_visitante(request.user):
        _encerrar_visitante(request)

    limpar_visitantes_expirados()
    user = criar_visitante()
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    messages.info(
        request,
        'Voce esta no modo visitante. Os dados sao ficticios e serao apagados ao sair.',
    )
    return redirect('dashboard')


def _encerrar_visitante(request):
    """
    Faz logout e apaga a conta temporaria do visitante (com alunos e mensalidades).
    """
    user = request.user
    logout(request)
    user.delete()


def logout_view(request):
    """
    View para logout
    """
    if is_visitante(request.user):
        _encerrar_visitante(request)
        if request.GET.get('next') == 'register':
            messages.info(request, 'Modo visitante encerrado. Crie sua conta para comecar.')
            return redirect('register')
        messages.success(request, 'Modo visitante encerrado. Os dados ficticios foram apagados.')
        return redirect('login')

    logout(request)
    messages.success(request, 'Voce foi desconectado.')
    return redirect('login')


@login_required(login_url='login')
def profile(request):
    """
    View para perfil do usuario
    """
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(
            user=request.user,
            escola_nome=request.user.first_name or 'Minha Escola'
        )
    
    if request.method == 'POST':
        form = PerfilForm(request.POST, user=request.user)
        if form.is_valid():
            dados = form.cleaned_data
            with transaction.atomic():
                profile.escola_nome = dados['escola_nome']
                profile.telefone = dados['telefone']
                profile.save()

                request.user.email = dados['email']
                request.user.first_name = dados['escola_nome'][:150]
                request.user.save()

            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('profile')
        exibir_erros_formulario(request, form)

    context = {
        'profile': profile,
    }
    return render(request, 'accounts/profile.html', context)


@login_required(login_url='login')
def upgrade(request):
    """
    View para pagina de upgrade de plano
    """
    return render(request, 'accounts/upgrade.html')

