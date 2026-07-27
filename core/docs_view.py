from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


@login_required
def docs_page(request):
    if not request.user.is_admin():
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect('dashboard')
    modules = [
        {
            'name': 'Autenticação',
            'icon': 'bi-shield-lock',
            'color': '#6366f1',
            'endpoints': [
                {'method': 'GET', 'url': '/login/', 'desc': 'Página de login do sistema', 'roles': 'Todos'},
                {'method': 'POST', 'url': '/login/', 'desc': 'Autenticar com usuário e senha', 'roles': 'Todos'},
                {'method': 'POST', 'url': '/logout/', 'desc': 'Encerrar a sessão', 'roles': 'Todos'},
                {'method': 'GET', 'url': '/profile/', 'desc': 'Visualizar perfil do usuário logado', 'roles': 'Todos'},
                {'method': 'GET', 'url': '/dashboard/', 'desc': 'Dashboard com métricas do sistema', 'roles': 'Todos'},
            ]
        },
        {
            'name': 'Usuários',
            'icon': 'bi-people',
            'color': '#ec4899',
            'endpoints': [
                {'method': 'GET', 'url': '/users/', 'desc': 'Listar todos os usuários', 'roles': 'Admin'},
                {'method': 'GET/POST', 'url': '/users/new/', 'desc': 'Criar usuário e vincular a funcionário', 'roles': 'Admin'},
                {'method': 'GET/POST', 'url': '/users/<id>/edit/', 'desc': 'Editar perfil, role e vínculo do usuário', 'roles': 'Admin'},
                {'method': 'GET/POST', 'url': '/users/<id>/reset-password/', 'desc': 'Redefinir senha de um usuário', 'roles': 'Admin'},
                {'method': 'POST', 'url': '/users/<id>/toggle-active/', 'desc': 'Ativar ou desativar conta', 'roles': 'Admin'},
                {'method': 'GET/POST', 'url': '/users/<id>/delete/', 'desc': 'Excluir usuário permanentemente', 'roles': 'Admin'},
            ]
        },
        {
            'name': 'PIM — Funcionários',
            'icon': 'bi-person-badge',
            'color': '#f97316',
            'endpoints': [
                {'method': 'GET', 'url': '/pim/', 'desc': 'Lista funcionários (ESS: redireciona pro próprio perfil)', 'roles': 'Supervisor, Admin'},
                {'method': 'GET', 'url': '/pim/<id>/', 'desc': 'Perfil completo: dados pessoais, contato, salário, dependentes, qualificações', 'roles': 'ESS (só o próprio), Supervisor, Admin'},
                {'method': 'GET/POST', 'url': '/pim/add/', 'desc': 'Cadastrar novo funcionário', 'roles': 'Supervisor, Admin'},
                {'method': 'GET/POST', 'url': '/pim/<id>/personal/', 'desc': 'Editar dados pessoais', 'roles': 'Supervisor, Admin'},
                {'method': 'GET/POST', 'url': '/pim/<id>/job/', 'desc': 'Editar cargo, departamento, turno e status', 'roles': 'Supervisor, Admin'},
                {'method': 'GET/POST', 'url': '/pim/<id>/contact/', 'desc': 'Editar telefones e endereço', 'roles': 'Supervisor, Admin'},
                {'method': 'POST', 'url': '/pim/<id>/photo/', 'desc': 'Upload de foto do funcionário', 'roles': 'Supervisor, Admin'},
                {'method': 'GET/POST', 'url': '/pim/<id>/terminate/', 'desc': 'Registrar desligamento', 'roles': 'Admin'},
                {'method': 'GET/POST', 'url': '/pim/<id>/dependent/add/', 'desc': 'Adicionar dependente', 'roles': 'Supervisor, Admin'},
                {'method': 'GET/POST', 'url': '/pim/<id>/emergency/add/', 'desc': 'Adicionar contato de emergência', 'roles': 'Supervisor, Admin'},
                {'method': 'GET/POST', 'url': '/pim/<id>/salary/add/', 'desc': 'Adicionar histórico salarial', 'roles': 'Admin'},
            ]
        },
        {
            'name': 'Ponto (Attendance)',
            'icon': 'bi-clock-history',
            'color': '#10b981',
            'endpoints': [
                {'method': 'GET', 'url': '/attendance/my/', 'desc': 'Meu ponto: relógio, entrada/saída e histórico pessoal', 'roles': 'Todos'},
                {'method': 'POST', 'url': '/attendance/punch-in/', 'desc': 'Registrar entrada (punch-in)', 'roles': 'Todos'},
                {'method': 'POST', 'url': '/attendance/punch-out/', 'desc': 'Registrar saída (punch-out)', 'roles': 'Todos'},
                {'method': 'GET', 'url': '/attendance/', 'desc': 'Todos os registros de ponto da equipe', 'roles': 'Supervisor, Admin'},
            ]
        },
        {
            'name': 'Licenças (Leave)',
            'icon': 'bi-calendar-check',
            'color': '#3b82f6',
            'endpoints': [
                {'method': 'GET', 'url': '/leave/', 'desc': 'Licenças da equipe (Supervisor) ou somente as próprias (ESS)', 'roles': 'Todos'},
                {'method': 'GET', 'url': '/leave/?mine=1', 'desc': 'Forçar visualização apenas das próprias licenças', 'roles': 'Supervisor, Admin'},
                {'method': 'GET/POST', 'url': '/leave/apply/', 'desc': 'Solicitar nova licença (férias, médica, etc.)', 'roles': 'Todos'},
                {'method': 'GET', 'url': '/leave/<id>/', 'desc': 'Detalhes da solicitação de licença', 'roles': 'Todos (própria), Supervisor (qualquer)'},
                {'method': 'POST', 'url': '/leave/<id>/approve/', 'desc': 'Aprovar licença', 'roles': 'Supervisor, Admin'},
                {'method': 'POST', 'url': '/leave/<id>/reject/', 'desc': 'Rejeitar licença', 'roles': 'Supervisor, Admin'},
                {'method': 'POST', 'url': '/leave/<id>/cancel/', 'desc': 'Cancelar solicitação de licença', 'roles': 'Todos (própria)'},
                {'method': 'GET', 'url': '/leave/types/', 'desc': 'Tipos de licença (ex: Férias, Médica, Maternidade)', 'roles': 'Admin'},
                {'method': 'GET/POST', 'url': '/leave/types/add/', 'desc': 'Criar tipo de licença', 'roles': 'Admin'},
                {'method': 'GET', 'url': '/leave/holidays/', 'desc': 'Feriados cadastrados', 'roles': 'Admin'},
                {'method': 'GET/POST', 'url': '/leave/holidays/add/', 'desc': 'Adicionar feriado', 'roles': 'Admin'},
            ]
        },
        {
            'name': 'Reembolsos (Claim)',
            'icon': 'bi-receipt',
            'color': '#8b5cf6',
            'endpoints': [
                {'method': 'GET', 'url': '/claim/', 'desc': 'Reembolsos (ESS: próprios; Supervisor: todos)', 'roles': 'Todos'},
                {'method': 'GET/POST', 'url': '/claim/new/', 'desc': 'Abrir nova solicitação de reembolso de despesa', 'roles': 'Todos'},
                {'method': 'GET', 'url': '/claim/<id>/', 'desc': 'Detalhe do reembolso com despesas, anexos e status', 'roles': 'Todos (próprio), Supervisor (qualquer)'},
                {'method': 'POST', 'url': '/claim/<id>/approve/', 'desc': 'Aprovar reembolso', 'roles': 'Supervisor, Admin'},
                {'method': 'POST', 'url': '/claim/<id>/reject/', 'desc': 'Rejeitar reembolso', 'roles': 'Supervisor, Admin'},
            ]
        },
        {
            'name': 'Recrutamento',
            'icon': 'bi-briefcase',
            'color': '#f59e0b',
            'endpoints': [
                {'method': 'GET', 'url': '/recruitment/vacancies/', 'desc': 'Listar vagas abertas', 'roles': 'Supervisor, Admin'},
                {'method': 'GET/POST', 'url': '/recruitment/vacancies/add/', 'desc': 'Criar nova vaga', 'roles': 'Supervisor, Admin'},
                {'method': 'GET', 'url': '/recruitment/vacancies/<id>/', 'desc': 'Vaga com lista de candidatos', 'roles': 'Supervisor, Admin'},
                {'method': 'GET', 'url': '/recruitment/candidates/', 'desc': 'Lista geral de candidatos', 'roles': 'Supervisor, Admin'},
                {'method': 'GET', 'url': '/recruitment/candidates/<id>/', 'desc': 'Perfil do candidato com histórico', 'roles': 'Supervisor, Admin'},
                {'method': 'POST', 'url': '/recruitment/candidates/<id>/status/', 'desc': 'Atualizar status no processo seletivo', 'roles': 'Supervisor, Admin'},
            ]
        },
        {
            'name': 'Desempenho (Performance)',
            'icon': 'bi-star',
            'color': '#ef4444',
            'endpoints': [
                {'method': 'GET', 'url': '/performance/reviews/', 'desc': 'Avaliações de desempenho', 'roles': 'Supervisor, Admin'},
                {'method': 'GET/POST', 'url': '/performance/reviews/add/', 'desc': 'Criar avaliação', 'roles': 'Supervisor, Admin'},
                {'method': 'GET', 'url': '/performance/kpis/', 'desc': 'KPIs cadastrados', 'roles': 'Supervisor, Admin'},
                {'method': 'GET/POST', 'url': '/performance/kpis/add/', 'desc': 'Criar indicador KPI', 'roles': 'Supervisor, Admin'},
                {'method': 'GET', 'url': '/performance/trackers/', 'desc': 'Rastreadores de desempenho', 'roles': 'Supervisor, Admin'},
            ]
        },
        {
            'name': 'Buzz (Rede Social)',
            'icon': 'bi-chat-heart',
            'color': '#06b6d4',
            'endpoints': [
                {'method': 'GET', 'url': '/buzz/', 'desc': 'Feed da empresa: posts, fotos, comentários e curtidas', 'roles': 'Todos'},
                {'method': 'POST', 'url': '/buzz/post/', 'desc': 'Publicar post ou foto no feed', 'roles': 'Todos'},
                {'method': 'POST', 'url': '/buzz/post/<id>/like/', 'desc': 'Curtir ou descurtir publicação', 'roles': 'Todos'},
                {'method': 'POST', 'url': '/buzz/post/<id>/comment/', 'desc': 'Comentar em publicação', 'roles': 'Todos'},
                {'method': 'POST', 'url': '/buzz/post/<id>/delete/', 'desc': 'Apagar publicação (somente autor ou admin)', 'roles': 'Autor / Admin'},
            ]
        },
        {
            'name': 'Administração',
            'icon': 'bi-building',
            'color': '#64748b',
            'endpoints': [
                {'method': 'GET/POST', 'url': '/admin-panel/organization/', 'desc': 'Dados da organização (nome, CNPJ, endereço, logotipo)', 'roles': 'Admin'},
                {'method': 'GET', 'url': '/admin-panel/job-titles/', 'desc': 'Cargos cadastrados', 'roles': 'Admin'},
                {'method': 'GET/POST', 'url': '/admin-panel/job-titles/add/', 'desc': 'Criar cargo', 'roles': 'Admin'},
                {'method': 'GET', 'url': '/admin-panel/locations/', 'desc': 'Localizações/filiais', 'roles': 'Admin'},
                {'method': 'GET/POST', 'url': '/admin-panel/locations/add/', 'desc': 'Nova localização', 'roles': 'Admin'},
                {'method': 'GET', 'url': '/admin-panel/subunits/', 'desc': 'Departamentos com hierarquia pai/filho', 'roles': 'Admin'},
                {'method': 'GET/POST', 'url': '/admin-panel/subunits/add/', 'desc': 'Criar departamento', 'roles': 'Admin'},
            ]
        },
    ]
    return render(request, 'core/docs.html', {'modules': modules})

@login_required
def guia_dev_page(request):
    """View para o guia estático e explicativo da arquitetura PIM."""
    if not request.user.is_admin():
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect('dashboard')
    return render(request, 'core/guia_dev.html')
