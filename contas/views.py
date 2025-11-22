from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import ContaPagar, Categoria
from .forms import ContaPagarForm, NovaContaForm, CriarUsuarioForm, RecuperarSenhaForm, QuitarContaForm
from django.db.models import Sum
from django_filters.views import FilterView
import django_filters
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
import uuid
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.core.mail import send_mail
from django.conf import settings
import random
import string
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.template.loader import get_template

# Create your views here.

class ContaPagarFilter(django_filters.FilterSet):
    descricao = django_filters.CharFilter(lookup_expr='icontains', label='Buscar por Descrição')
    # Excluir 'pago' das opções de status, pois contas quitadas não aparecem na lista
    status = django_filters.ChoiceFilter(
        choices=[(k, v) for k, v in ContaPagar.STATUS_CHOICES if k != 'pago'],
        label='Status'
    )
    categoria = django_filters.ModelChoiceFilter(queryset=Categoria.objects.all(), label='Categoria')
    valor = django_filters.NumberFilter(field_name='valor', label='Buscar por Valor')
    vencimento = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = ContaPagar
        fields = ['status', 'categoria', 'vencimento', 'descricao', 'valor']

@login_required
def lista_contas(request):
    # Filtrar apenas contas em aberto (excluir quitadas)
    contas_list = ContaPagar.objects.filter(
        usuario=request.user
    ).exclude(
        status='pago'
    ).select_related('categoria').order_by('grupo_parcelamento', 'numero_parcela')

    # Atualiza status de todas as contas do usuário antes de exibir
    for conta in contas_list:
        conta.save()

    filtro = ContaPagarFilter(request.GET, queryset=contas_list)
    
    # Obter queryset filtrado
    queryset_filtrado = filtro.qs
    
    # Ordenação
    ordenacao = request.GET.get('ordenar', '')
    if ordenacao:
        if ordenacao == 'status':
            queryset_filtrado = queryset_filtrado.order_by('status', 'vencimento')
        elif ordenacao == '-status':
            queryset_filtrado = queryset_filtrado.order_by('-status', 'vencimento')
        elif ordenacao == 'valor':
            queryset_filtrado = queryset_filtrado.order_by('valor')
        elif ordenacao == '-valor':
            queryset_filtrado = queryset_filtrado.order_by('-valor')
        elif ordenacao == 'vencimento':
            queryset_filtrado = queryset_filtrado.order_by('vencimento')
        elif ordenacao == '-vencimento':
            queryset_filtrado = queryset_filtrado.order_by('-vencimento')
        elif ordenacao == 'descricao':
            queryset_filtrado = queryset_filtrado.order_by('descricao')
        elif ordenacao == '-descricao':
            queryset_filtrado = queryset_filtrado.order_by('-descricao')
        elif ordenacao == 'categoria':
            queryset_filtrado = queryset_filtrado.order_by('categoria__nome')
        elif ordenacao == '-categoria':
            queryset_filtrado = queryset_filtrado.order_by('-categoria__nome')
    
    # Aplicar Paginação
    paginator = Paginator(queryset_filtrado, 15) # 15 contas por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Dashboard - usar queryset filtrado para cálculos de contas em aberto
    hoje = timezone.now()
    total_em_dia = queryset_filtrado.filter(status='pendente').aggregate(Sum('valor'))['valor__sum'] or 0
    total_vencido = queryset_filtrado.filter(status='vencida').aggregate(Sum('valor'))['valor__sum'] or 0
    # Para contas quitadas, buscar diretamente do banco (não estão no queryset filtrado)
    total_quitado_mes = ContaPagar.objects.filter(
        usuario=request.user,
        status='pago',
        atualizado_em__month=hoje.month,
        atualizado_em__year=hoje.year
    ).aggregate(Sum('valor'))['valor__sum'] or 0
    total = queryset_filtrado.aggregate(Sum('valor'))['valor__sum'] or 0

    # Garantir 2 casas decimais
    total_em_dia = float(f'{total_em_dia:.2f}')
    total_vencido = float(f'{total_vencido:.2f}')
    total_quitado_mes = float(f'{total_quitado_mes:.2f}')
    total = float(f'{total:.2f}')
    
    return render(request, 'contas/lista_contas.html', {
        'filtro': filtro,
        'page_obj': page_obj, 
        'total': total,
        'total_em_dia': total_em_dia,
        'total_vencido': total_vencido,
        'total_quitado_mes': total_quitado_mes
    })

@login_required
def historico_contas_quitadas(request):
    # Filtrar apenas contas quitadas
    contas_list = ContaPagar.objects.filter(
        usuario=request.user,
        status='pago'
    ).select_related('categoria').order_by('-atualizado_em', 'grupo_parcelamento', 'numero_parcela')

    # Filtros simples para histórico
    descricao = request.GET.get('descricao', '')
    if descricao:
        contas_list = contas_list.filter(descricao__icontains=descricao)
    
    categoria_id = request.GET.get('categoria', '')
    if categoria_id:
        contas_list = contas_list.filter(categoria_id=categoria_id)
    
    # Ordenação
    ordenacao = request.GET.get('ordenar', '')
    if ordenacao:
        if ordenacao == 'valor':
            contas_list = contas_list.order_by('valor')
        elif ordenacao == '-valor':
            contas_list = contas_list.order_by('-valor')
        elif ordenacao == 'vencimento':
            contas_list = contas_list.order_by('vencimento')
        elif ordenacao == '-vencimento':
            contas_list = contas_list.order_by('-vencimento')
        elif ordenacao == 'descricao':
            contas_list = contas_list.order_by('descricao')
        elif ordenacao == '-descricao':
            contas_list = contas_list.order_by('-descricao')
        elif ordenacao == 'categoria':
            contas_list = contas_list.order_by('categoria__nome')
        elif ordenacao == '-categoria':
            contas_list = contas_list.order_by('-categoria__nome')
        elif ordenacao == 'data_quitacao':
            contas_list = contas_list.order_by('-atualizado_em')
        elif ordenacao == '-data_quitacao':
            contas_list = contas_list.order_by('atualizado_em')
    
    # Aplicar Paginação
    paginator = Paginator(contas_list, 15) # 15 contas por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Estatísticas do histórico
    total_quitado = contas_list.aggregate(Sum('valor'))['valor__sum'] or 0
    total_quitado = float(f'{total_quitado:.2f}')
    
    # Buscar todas as categorias para o filtro
    categorias = Categoria.objects.all()
    
    return render(request, 'contas/historico_quitadas.html', {
        'page_obj': page_obj,
        'total_quitado': total_quitado,
        'categorias': categorias,
        'descricao_filtro': descricao,
        'categoria_filtro': categoria_id
    })

@login_required
def exportar_pdf_contas(request):
    """Exporta relatório PDF de contas em aberto"""
    try:
        from xhtml2pdf import pisa
        from io import BytesIO
    except ImportError:
        messages.error(request, 'Biblioteca xhtml2pdf não está instalada. Execute: pip install xhtml2pdf')
        return redirect('lista_contas')
    
    # Aplicar os mesmos filtros da lista
    contas_list = ContaPagar.objects.filter(
        usuario=request.user
    ).exclude(
        status='pago'
    ).select_related('categoria').order_by('grupo_parcelamento', 'numero_parcela')

    # Aplicar filtros da query string
    descricao = request.GET.get('descricao', '')
    if descricao:
        contas_list = contas_list.filter(descricao__icontains=descricao)
    
    status_filtro = request.GET.get('status', '')
    if status_filtro:
        contas_list = contas_list.filter(status=status_filtro)
    
    categoria_id = request.GET.get('categoria', '')
    if categoria_id:
        contas_list = contas_list.filter(categoria_id=categoria_id)
    
    # Calcular totais
    hoje = timezone.now()
    total_em_dia = contas_list.filter(status='pendente').aggregate(Sum('valor'))['valor__sum'] or 0
    total_vencido = contas_list.filter(status='vencida').aggregate(Sum('valor'))['valor__sum'] or 0
    total = contas_list.aggregate(Sum('valor'))['valor__sum'] or 0
    
    # Garantir 2 casas decimais
    total_em_dia = float(f'{total_em_dia:.2f}')
    total_vencido = float(f'{total_vencido:.2f}')
    total = float(f'{total:.2f}')
    
    # Renderizar template HTML
    template = get_template('contas/pdf_contas_aberto.html')
    html_content = template.render({
        'contas': contas_list,
        'total_em_dia': total_em_dia,
        'total_vencido': total_vencido,
        'total': total,
        'data_geracao': timezone.now(),
        'usuario': request.user
    })
    
    # Gerar PDF
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_content.encode("UTF-8")), result)
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        filename = f'contas_aberto_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    else:
        messages.error(request, 'Erro ao gerar PDF. Tente novamente.')
        return redirect('lista_contas')

@login_required
def exportar_pdf_historico(request):
    """Exporta relatório PDF do histórico de contas quitadas"""
    try:
        from xhtml2pdf import pisa
        from io import BytesIO
    except ImportError:
        messages.error(request, 'Biblioteca xhtml2pdf não está instalada. Execute: pip install xhtml2pdf')
        return redirect('historico_quitadas')
    
    # Aplicar os mesmos filtros do histórico
    contas_list = ContaPagar.objects.filter(
        usuario=request.user,
        status='pago'
    ).select_related('categoria').order_by('-atualizado_em', 'grupo_parcelamento', 'numero_parcela')

    # Aplicar filtros da query string
    descricao = request.GET.get('descricao', '')
    if descricao:
        contas_list = contas_list.filter(descricao__icontains=descricao)
    
    categoria_id = request.GET.get('categoria', '')
    if categoria_id:
        contas_list = contas_list.filter(categoria_id=categoria_id)
    
    # Calcular total
    total_quitado = contas_list.aggregate(Sum('valor'))['valor__sum'] or 0
    total_quitado = float(f'{total_quitado:.2f}')
    
    # Renderizar template HTML
    template = get_template('contas/pdf_historico_quitadas.html')
    html_content = template.render({
        'contas': contas_list,
        'total_quitado': total_quitado,
        'data_geracao': timezone.now(),
        'usuario': request.user
    })
    
    # Gerar PDF
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_content.encode("UTF-8")), result)
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        filename = f'historico_quitadas_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    else:
        messages.error(request, 'Erro ao gerar PDF. Tente novamente.')
        return redirect('historico_quitadas')

@login_required
def nova_conta(request):
    contas = ContaPagar.objects.filter(usuario=request.user)
    hoje = timezone.now()
    total_em_dia = contas.filter(status='pendente').aggregate(Sum('valor'))['valor__sum'] or 0
    total_vencido = contas.filter(status='vencida').aggregate(Sum('valor'))['valor__sum'] or 0
    total_quitado_mes = contas.filter(
        status='pago',
        atualizado_em__month=hoje.month,
        atualizado_em__year=hoje.year
    ).aggregate(Sum('valor'))['valor__sum'] or 0

    if request.method == 'POST':
        form = NovaContaForm(request.POST)
        if form.is_valid():
            form.instance.usuario = request.user
            if form.cleaned_data.get('tipo_pagamento') == 'avista':
                form.save()
            else:
                # Parcelado: lógica já existente
                descricao = form.cleaned_data['descricao']
                valor = form.cleaned_data['valor']
                vencimento = form.cleaned_data['vencimento']
                categoria = form.cleaned_data['categoria']
                observacao = form.cleaned_data['observacao']
                numero_parcelas = form.cleaned_data['numero_parcelas']
                grupo_parcelamento = uuid.uuid4()
                for i in range(numero_parcelas):
                    parcela = ContaPagar(
                        usuario=request.user,
                        descricao=descricao,
                        valor=valor / numero_parcelas,
                        vencimento=vencimento + relativedelta(months=i),
                        categoria=categoria,
                        observacao=observacao,
                        grupo_parcelamento=grupo_parcelamento,
                        numero_parcela=i+1,
                        total_parcelas=numero_parcelas
                    )
                    parcela.save()
            messages.success(request, 'Conta cadastrada com sucesso!')
            return redirect('lista_contas')
    else:
        form = NovaContaForm()
    return render(request, 'contas/conta_form.html', {
        'form': form,
        'total_em_dia': total_em_dia,
        'total_vencido': total_vencido,
        'total_quitado_mes': total_quitado_mes
    })

@login_required
def editar_conta(request, pk):
    conta = get_object_or_404(ContaPagar, pk=pk, usuario=request.user)
    if conta.status == 'pago':
        messages.error(request, 'Contas já quitadas não podem ser editadas.')
        return redirect('lista_contas')
    if request.method == 'POST':
        form = ContaPagarForm(request.POST, instance=conta)
        if form.is_valid():
            form.save()
            messages.success(request, 'Conta atualizada com sucesso!')
            return redirect('lista_contas')
    else:
        form = ContaPagarForm(instance=conta)
    return render(request, 'contas/conta_form.html', {'form': form})

@login_required
def deletar_conta(request, conta_id):
    conta = get_object_or_404(ContaPagar, pk=conta_id, usuario=request.user)
    if conta.status == 'pago':
        messages.error(request, 'Contas já quitadas não podem ser excluídas.')
        return redirect('lista_contas')
    if request.method == 'POST':
        conta.delete()
        return redirect('lista_contas')
    return render(request, 'contas/confirmar_delete.html', {'conta': conta})

@user_passes_test(lambda u: u.is_superuser)
def reabrir_conta(request, pk):
    conta = get_object_or_404(ContaPagar, pk=pk)
    if conta.status == 'pago':
        conta.status = 'pendente'
        conta.save()
        messages.success(request, 'Conta reaberta com sucesso!')
    else:
        messages.info(request, 'A conta não está quitada.')
    return redirect('lista_contas')

@login_required
def quitar_conta(request, conta_id):
    conta = get_object_or_404(ContaPagar, pk=conta_id, usuario=request.user)
    
    if conta.status == 'pago':
        messages.warning(request, f'A conta "{conta.descricao}" já estava quitada.')
        return redirect('lista_contas')
    
    # Verificar se a conta está vencida
    conta_vencida = conta.status == 'vencida'
    
    if request.method == 'POST':
        form = QuitarContaForm(request.POST, conta_vencida=conta_vencida, valor_original=conta.valor)
        if form.is_valid():
            conta.status = 'pago'
            conta.info_pagamento = form.cleaned_data['info_pagamento']
            
            # Se houver valor atualizado informado, atualizar o valor
            valor_atualizado = form.cleaned_data.get('valor_atualizado')
            if valor_atualizado and valor_atualizado != conta.valor:
                valor_original = conta.valor
                conta.valor = valor_atualizado
                # Adicionar informação sobre o valor original no info_pagamento
                info_adicional = f'\n\nValor original: R$ {valor_original:.2f}\nValor pago: R$ {valor_atualizado:.2f}'
                if conta_vencida:
                    info_adicional = f'\n\nValor original: R$ {valor_original:.2f}\nValor pago (com juros): R$ {valor_atualizado:.2f}'
                
                if conta.info_pagamento:
                    conta.info_pagamento += info_adicional
                else:
                    conta.info_pagamento = info_adicional.strip()
                conta.save(update_fields=['status', 'info_pagamento', 'valor', 'atualizado_em'])
                if conta_vencida:
                    messages.success(request, f'A conta "{conta.descricao}" foi quitada com valor atualizado de R$ {valor_atualizado:.2f} (incluindo juros).')
                else:
                    messages.success(request, f'A conta "{conta.descricao}" foi quitada com valor de R$ {valor_atualizado:.2f}.')
            else:
                conta.save(update_fields=['status', 'info_pagamento', 'atualizado_em'])
                messages.success(request, f'A conta "{conta.descricao}" foi marcada como quitada.')
            return redirect('lista_contas')
    else:
        form = QuitarContaForm(conta_vencida=conta_vencida, valor_original=conta.valor)
    
    return render(request, 'contas/quitar_conta.html', {
        'conta': conta,
        'form': form,
        'conta_vencida': conta_vencida
    })

@csrf_exempt
@login_required
def editar_inline(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            conta_id = data.get('id')
            campo = data.get('campo')
            valor = data.get('valor')
            conta = ContaPagar.objects.get(pk=conta_id, usuario=request.user)
            valor_antigo = getattr(conta, campo)
            if campo == 'valor':
                try:
                    valor_float = float(valor)
                    if valor_float <= 0:
                        raise ValueError
                    conta.valor = valor_float
                except Exception:
                    return JsonResponse({'sucesso': False, 'erro': 'Valor inválido.', 'valor_antigo': f'R$ {valor_antigo:.2f}'})
            elif campo == 'vencimento':
                try:
                    # Espera formato dd/mm/yyyy
                    dt = datetime.strptime(valor, '%d/%m/%Y').date()
                    conta.vencimento = dt
                except Exception:
                    return JsonResponse({'sucesso': False, 'erro': 'Data inválida.', 'valor_antigo': valor_antigo.strftime('%d/%m/%Y')})
            else:
                return JsonResponse({'sucesso': False, 'erro': 'Campo inválido.', 'valor_antigo': valor_antigo})
            conta.save()
            if campo == 'valor':
                return JsonResponse({'sucesso': True})
            elif campo == 'vencimento':
                return JsonResponse({'sucesso': True, 'valor_formatado': conta.vencimento.strftime('%d/%m/%Y')})
        except Exception as e:
            return JsonResponse({'sucesso': False, 'erro': 'Erro ao salvar.'})
    return JsonResponse({'sucesso': False, 'erro': 'Requisição inválida.'})

def gerar_senha_aleatoria(tamanho=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(tamanho))

def criar_usuario(request):
    if request.method == 'POST':
        form = CriarUsuarioForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            senha = form.cleaned_data['senha1']
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Usuário já existe.')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'E-mail já cadastrado.')
            else:
                user = User.objects.create_user(username=username, email=email, password=senha, is_active=True)
                messages.success(request, 'Usuário criado com sucesso! Faça login para acessar o sistema.')
                return redirect('login')
    else:
        form = CriarUsuarioForm()
    return render(request, 'registration/criar_usuario.html', {'form': form})

def recuperar_senha(request):
    if request.method == 'POST':
        form = RecuperarSenhaForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                senha = gerar_senha_aleatoria()
                user.set_password(senha)
                user.save()
                user.profile.must_change_password = True
                user.profile.save()
                
                try:
                    send_mail(
                        'Recuperação de senha - PayFlow',
                        f'Sua nova senha provisória: {senha}\n\nVocê será obrigado a trocar esta senha no próximo login.',
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=False,
                    )
                    messages.success(request, 'Nova senha enviada para seu e-mail.')
                except Exception as e:
                    messages.error(request, f'Erro ao enviar e-mail: {str(e)}')
                    return redirect('recuperar_senha')
                    
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'E-mail não encontrado.')
    else:
        form = RecuperarSenhaForm()
    return render(request, 'registration/recuperar_senha.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def form_valid(self, form):
        user = form.get_user()
        if hasattr(user, 'profile') and user.profile.must_change_password:
            self.request.session['force_password_change'] = True
            from django.contrib.auth import login
            login(self.request, user)
            return redirect('trocar_senha_obrigatorio')
        return super().form_valid(form)

def trocar_senha_obrigatorio(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        senha1 = request.POST.get('nova_senha1')
        senha2 = request.POST.get('nova_senha2')
        if not senha1 or not senha2:
            messages.error(request, 'Preencha os dois campos de senha.')
        elif senha1 != senha2:
            messages.error(request, 'As senhas não coincidem.')
        else:
            user = request.user
            user.set_password(senha1)
            user.save()
            user.profile.must_change_password = False
            user.profile.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Senha alterada com sucesso!')
            return redirect('lista_contas')
    return render(request, 'registration/trocar_senha_obrigatorio.html')
