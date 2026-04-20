from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile


def register(request):
    """
    View para registro de novo usuario (escola)
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        escola_nome = request.POST.get('escola_nome')
        telefone = request.POST.get('telefone')
        
        # Validacoes
        if password != password_confirm:
            messages.error(request, 'As senhas nao conferem.')
            return redirect('register')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Este usuario ja existe.')
            return redirect('register')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Este email ja esta registrado.')
            return redirect('register')
        
        # Criar usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=escola_nome
        )
        
        # Criar perfil
        UserProfile.objects.create(
            user=user,
            escola_nome=escola_nome,
            telefone=telefone
        )
        
        messages.success(request, 'Registro realizado com sucesso! Faca login.')
        return redirect('login')
    
    return render(request, 'accounts/register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Bem-vindo, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario ou senha invalidos.')
    
    return render(request, 'accounts/login.html')


def logout_view(request):
    """
    View para logout
    """
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
        profile.escola_nome = request.POST.get('escola_nome', profile.escola_nome)
        profile.telefone = request.POST.get('telefone', profile.telefone)
        profile.save()
        
        request.user.email = request.POST.get('email', request.user.email)
        request.user.save()
        
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('profile')
    
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