# CDC Core — Plataforma Operacional

Sistema central da **CDC** — plataforma Django multi-app para automação de operações internas: ponto eletrônico, monitoramento de contas Gmail e ferramentas de produtividade do dia a dia.

---

## 🗂️ Apps do Projeto

| App | Descrição | Status |
| :--- | :--- | :--- |
| `core` | Usuários, autenticação, middleware e APIs base | ✅ Ativo |
| `pim` | Gestão de informações pessoais (PIM) | ✅ Ativo |
| `attendance` | Registro e espelho de ponto eletrônico | ✅ Ativo |
| `time_tracking` | Banco de horas e rastreamento de jornada | ✅ Ativo |
| `leave` | Folgas, licenças e ausências | ✅ Ativo |
| `buzz` | Feed de comunicação interna (Netgram) | ✅ Ativo |
| `agenda` | Agendamento de salas, veículos e eventos | ✅ Ativo |
| `claim` | Reembolsos e despesas corporativas | ✅ Ativo |
| `payroll` | Folha de pagamento | ✅ Ativo |
| `performance` | Avaliações de desempenho | ✅ Ativo |
| `recruitment` | Recrutamento e seleção | ✅ Ativo |
| `emails` | Templates e envio de e-mails | ✅ Ativo |
| `admin_app` | Painel administrativo customizado | ✅ Ativo |

### 🔜 Apps Planejados

| App | Descrição | Status |
| :--- | :--- | :--- |
| `relogio` | Relógio de ponto mobile/web com geolocalização | 🔲 Planejado |
| `gmail_monitor` | Acompanhamento e triagem de contas Gmail da equipe | 🔲 Planejado |
| `toolbox` | Ferramentas avulsas de produtividade e automação do dia a dia | 🔲 Planejado |

---

## 🛠️ Stack Tecnológico

- **Backend:** Python 3.x / Django 5.2
- **Banco de Dados:** PostgreSQL (Neon Serverless)
- **Autenticação:** JWT (`djangorestframework-simplejwt`) + `django-axes`
- **API:** Django REST Framework + drf-spectacular (OpenAPI)
- **Armazenamento de Mídia:** Cloudinary
- **E-mail:** Resend via `django-anymail`
- **Push Notifications:** Firebase Cloud Messaging
- **Multi-tenancy:** `django-tenants`

---

## 🚀 Instalação Local

```bash
# 1. Clone o repositório
git clone git@github.com:dxcdc/Core.git
cd Core

# 2. Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com as credenciais reais

# 5. Rode as migrações
python manage.py migrate

# 6. Crie um superusuário
python manage.py createsuperuser

# 7. Inicie o servidor
python manage.py runserver
```

---

## 📁 Estrutura de Diretórios

```text
Core/
├── NetlineRH/          # Settings, URLs raiz, WSGI/ASGI
├── core/               # App base: usuários, auth, middleware
├── pim/                # Informações pessoais
├── attendance/         # Ponto eletrônico
├── time_tracking/      # Banco de horas
├── leave/              # Folgas e licenças
├── buzz/               # Feed interno
├── agenda/             # Agendamentos
├── claim/              # Reembolsos
├── payroll/            # Folha de pagamento
├── performance/        # Avaliações
├── recruitment/        # Recrutamento
├── emails/             # Templates de e-mail
├── admin_app/          # Admin customizado
├── templates/          # Templates HTML globais
├── static/             # Arquivos estáticos
├── media/              # Uploads (não versionado)
├── manage.py
├── requirements.txt
├── .env.example        # Template de variáveis de ambiente
├── .gitignore
├── SECURITY.md
└── LICENSE
```

---

## 🔐 Segurança

Nunca suba arquivos `.env`, certificados `.pem` ou senhas para o Git.
Consulte [SECURITY.md](SECURITY.md) para reportar vulnerabilidades.

---

## 📄 Licença

Distribuído sob a licença definida em [LICENSE](LICENSE).
