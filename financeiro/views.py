from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from accounts.decorators import plano_profissional_required
from .models import Mensalidade
from core.models import Aluno
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from .serializers import MensalidadeBulkSerializer


def _atualizar_status_mensalidades(usuario):
    hoje = timezone.now().date()
    Mensalidade.objects.filter(
        usuario=usuario,
        status='pendente',
        data_vencimento__lt=hoje,
    ).update(status='atrasado')
    Mensalidade.objects.filter(
        usuario=usuario,
        status='atrasado',
        data_vencimento__gte=hoje,
    ).update(status='pendente')


def _get_mes_selecionado(request):
    hoje = timezone.now().date()
    mes_param = request.GET.get('mes')

    if mes_param:
        try:
            ano, mes = map(int, mes_param.split('-'))
            return datetime(ano, mes, 1).date()
        except (ValueError, IndexError):
            pass

    return datetime(hoje.year, hoje.month, 1).date()


def _get_meses_disponiveis(mes_selecionado):
    hoje = timezone.now().date()
    meses_disponiveis = []
    data_temp = datetime(hoje.year, hoje.month, 1).date()
    meses_pt = {
        'January': 'Janeiro',
        'February': 'Fevereiro',
        'March': 'Março',
        'April': 'Abril',
        'May': 'Maio',
        'June': 'Junho',
        'July': 'Julho',
        'August': 'Agosto',
        'September': 'Setembro',
        'October': 'Outubro',
        'November': 'Novembro',
        'December': 'Dezembro',
    }

    for i in range(13):
        mes_nome = data_temp.strftime('%B')
        meses_disponiveis.append({
            'valor': data_temp.strftime('%Y-%m'),
            'label': f"{meses_pt.get(mes_nome, mes_nome)} {data_temp.strftime('%Y')}",
            'selecionado': data_temp == mes_selecionado,
        })
        data_temp = data_temp + relativedelta(months=1)

    return meses_disponiveis


@login_required(login_url='login')
def dashboard(request):
    _atualizar_status_mensalidades(request.user)

    mes_selecionado = _get_mes_selecionado(request)
    primeiro_dia = mes_selecionado
    ultimo_dia = (mes_selecionado + relativedelta(months=1)) - timedelta(days=1)

    total_pendente = Mensalidade.objects.filter(
        usuario=request.user,
        data_vencimento__gte=primeiro_dia,
        data_vencimento__lte=ultimo_dia,
        status__in=['pendente', 'atrasado'],
    ).aggregate(total=Sum('valor'))['total'] or 0

    total_pago = Mensalidade.objects.filter(
        usuario=request.user,
        data_vencimento__gte=primeiro_dia,
        data_vencimento__lte=ultimo_dia,
        status='pago',
    ).aggregate(total=Sum('valor'))['total'] or 0

    total_atrasado = Mensalidade.objects.filter(
        usuario=request.user,
        data_vencimento__gte=primeiro_dia,
        data_vencimento__lte=ultimo_dia,
        status='atrasado',
    ).aggregate(total=Sum('valor'))['total'] or 0

    context = {
        'total_pendente': total_pendente,
        'total_pago': total_pago,
        'total_atrasado': total_atrasado,
        'mes_selecionado': mes_selecionado.strftime('%Y-%m'),
        'meses_disponiveis': _get_meses_disponiveis(mes_selecionado),
    }
    return render(request, 'financeiro/dashboard.html', context)


@login_required(login_url='login')
def mensalidades_list(request):
    _atualizar_status_mensalidades(request.user)

    mensalidades = Mensalidade.objects.filter(usuario=request.user).select_related('aluno')
    status_filter = request.GET.get('status', 'todos')
    mes_filter = request.GET.get('mes', 'todos')
    busca = request.GET.get('busca', '').strip()

    if mes_filter and mes_filter != 'todos':
        try:
            ano, mes = map(int, mes_filter.split('-'))
            primeiro_dia = datetime(ano, mes, 1).date()
            ultimo_dia = (primeiro_dia + relativedelta(months=1)) - timedelta(days=1)
            mensalidades = mensalidades.filter(
                data_vencimento__gte=primeiro_dia,
                data_vencimento__lte=ultimo_dia,
            )
        except (ValueError, IndexError):
            mes_filter = 'todos'

    if status_filter == 'pagos':
        mensalidades = mensalidades.filter(status='pago')
    elif status_filter == 'pendentes':
        mensalidades = mensalidades.filter(status='pendente')
    elif status_filter == 'atrasados':
        mensalidades = mensalidades.filter(status='atrasado')

    if busca:
        mensalidades = mensalidades.filter(
            Q(aluno__nome__icontains=busca) |
            Q(aluno__responsavel__icontains=busca)
        )

    mensalidades = mensalidades.order_by('-data_vencimento')
    paginator = Paginator(mensalidades, 50)
    page_obj = paginator.get_page(request.GET.get('page'))

    meses_disponiveis = _get_meses_disponiveis(_get_mes_selecionado(request))
    for mes in meses_disponiveis:
        mes['selecionado'] = mes['valor'] == mes_filter

    context = {
        'page_obj': page_obj,
        'mensalidades': page_obj.object_list,
        'total_mensalidades': paginator.count,
        'status_filter': status_filter,
        'mes_filter': mes_filter,
        'busca': busca,
        'meses_disponiveis': meses_disponiveis,
    }
    return render(request, 'financeiro/mensalidades_list.html', context)


@login_required(login_url='login')
@plano_profissional_required
def mensalidade_create(request, aluno_id=None):
    """
    Criar nova mensalidade
    """
    aluno = None
    if aluno_id:
        aluno = get_object_or_404(Aluno, pk=aluno_id, usuario=request.user)

    if request.method == 'POST':
        aluno_id = request.POST.get('aluno')
        aluno = get_object_or_404(Aluno, pk=aluno_id, usuario=request.user)
        valor = request.POST.get('valor')
        data_vencimento = request.POST.get('data_vencimento')
        recorrente = request.POST.get('recorrente') == 'on'
        data_fim_recorrencia = request.POST.get('data_fim_recorrencia') or None

        Mensalidade.objects.create(
            usuario=request.user,
            aluno=aluno,
            valor=valor,
            data_vencimento=data_vencimento,
            recorrente=recorrente,
            data_fim_recorrencia=data_fim_recorrencia,
        )

        messages.success(request, f'Mensalidade de {aluno.nome} cadastrada com sucesso!')
        return redirect('mensalidades_list')

    alunos = Aluno.objects.filter(usuario=request.user).order_by('nome')

    context = {
        'alunos': alunos,
        'aluno': aluno,
    }
    return render(request, 'financeiro/mensalidade_form.html', context)


@login_required(login_url='login')
@plano_profissional_required
def mensalidade_update(request, pk):
    """
    Editar mensalidade
    """
    mensalidade = get_object_or_404(Mensalidade, pk=pk, usuario=request.user)

    if request.method == 'POST':
        mensalidade.valor = request.POST.get('valor', mensalidade.valor)
        mensalidade.data_vencimento = request.POST.get('data_vencimento', mensalidade.data_vencimento)
        mensalidade.status = request.POST.get('status', mensalidade.status)
        mensalidade.recorrente = request.POST.get('recorrente') == 'on'
        data_fim = request.POST.get('data_fim_recorrencia') or None
        mensalidade.data_fim_recorrencia = data_fim
        mensalidade.save()

        messages.success(request, 'Mensalidade atualizada com sucesso!')
        return redirect('mensalidades_list')

    context = {
        'mensalidade': mensalidade,
        'edit': True,
    }
    return render(request, 'financeiro/mensalidade_form.html', context)


@login_required(login_url='login')
@plano_profissional_required
def mensalidade_delete(request, pk):
    """
    Deletar mensalidade
    """
    mensalidade = get_object_or_404(Mensalidade, pk=pk, usuario=request.user)

    if request.method == 'POST':
        aluno_nome = mensalidade.aluno.nome
        mensalidade.delete()
        messages.success(request, f'Mensalidade de {aluno_nome} deletada com sucesso!')
        return redirect('mensalidades_list')

    context = {
        'mensalidade': mensalidade,
    }
    return render(request, 'financeiro/mensalidade_confirm_delete.html', context)


@login_required(login_url='login')
@plano_profissional_required
def mensalidade_pagar(request, pk):
    """
    Marcar mensalidade como paga
    """
    mensalidade = get_object_or_404(Mensalidade, pk=pk, usuario=request.user)

    if request.method == 'POST':
        mensalidade.marcar_como_pago()
        messages.success(request, f'Mensalidade de {mensalidade.aluno.nome} marcada como paga!')
        return redirect('mensalidades_list')

    context = {
        'mensalidade': mensalidade,
    }
    return render(request, 'financeiro/mensalidade_pagar.html', context)


@login_required(login_url='login')
@plano_profissional_required
def mensalidade_cobrar(request, pk):
    """
    Gerar link de cobranca via WhatsApp
    """
    mensalidade = get_object_or_404(Mensalidade, pk=pk, usuario=request.user)

    mensagem = mensalidade.get_whatsapp_message()
    link_whatsapp = mensalidade.aluno.get_whatsapp_link()

    import urllib.parse
    mensagem_encoded = urllib.parse.quote(mensagem)
    link_completo = f"{link_whatsapp}?text={mensagem_encoded}"

    context = {
        'mensalidade': mensalidade,
        'mensagem': mensagem,
        'link_whatsapp': link_completo,
    }
    return render(request, 'financeiro/mensalidade_cobrar.html', context)


######## API MENSALIDADES ########

class CadastroMassaMensalidadeView(APIView):

    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    def post(self, request):

        if not isinstance(request.data, list):
            return Response(
                {"error": "Envie uma lista de mensalidades"},
                status=400
            )

        serializer = MensalidadeBulkSerializer(data=request.data, many=True)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        mensalidades = [
            Mensalidade(**item)
            for item in serializer.validated_data
        ]

        Mensalidade.objects.bulk_create(mensalidades)

        return Response(
            {"message": f"{len(mensalidades)} mensalidades cadastradas com sucesso"},
            status=201
        )
