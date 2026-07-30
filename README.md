# CDC Relógio — Sistema de Ponto Eletrônico & Frequência

Sistema oficial de **Relógio de Ponto, Gestão de Frequência e Banco de Horas** do **Centro de Desenvolvimento e Cidadania (CDC)**.

---

## ⏱️ Funcionalidades Principais

- **Registro de Ponto Inteligente:** Batidas de entrada, almoço e saída com geolocalização e registro de IP.
- **Tratamento de Inconsistências:** Solicitação e aprovação de ajustes de batidas esquecidas com anexo de atestados.
- **Espelho de Ponto Eletrônico:** Emissão mensal de folhas de frequência prontas para conferência e assinatura.
- **Banco de Horas em Tempo Real:** Apuração automática de créditos e débitos de jornada.
- **Escalas e Turnos Flexíveis:** Padrões de escala (12x36, 5x2, 6x1) com suporte a trocas de turno e substituições.
- **Integração com Google Calendar:** Sincronização automática de escalas com calendários corporativos.

---

## 🛠️ Stack Tecnológica

- **Backend:** Python 3.13 / Django 5.2
- **Banco de Dados:** PostgreSQL (Neon Serverless) / SQLite (Fallback em Dev)
- **Autenticação:** JWT (`djangorestframework-simplejwt`) + `django-axes`
- **API:** Django REST Framework + drf-spectacular (OpenAPI / Swagger)
- **Notificações Push:** Firebase Cloud Messaging (FCM)
- **E-mail:** Resend via `django-anymail`

---

## 🚀 Instalação e Execução Local

```bash
# 1. Clone o repositório
git clone git@github.com:dxcdc/Relogio.git
cd Relogio

# 2. Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Rode as migrações
python manage.py migrate

# 5. Inicie o servidor local
python manage.py runserver
```

Acesse no navegador: **`http://127.0.0.1:8000/`**

---

## 📖 Documentação Completa

Acesse a pasta [`docs/funcionalidades/`](./docs/funcionalidades/) para visualizar os manuais procedimentais e diagramas de fluxo:

- ⏱️ [Manual do Ponto Eletrônico & Banco de Horas](./docs/funcionalidades/01_ponto_e_frequencia.md)
- 👥 [Manual de Cadastro de Funcionários & Organograma](./docs/funcionalidades/02_pim_colaboradores.md)
- 🏖️ [Manual de Férias e Ausências](./docs/funcionalidades/03_folgas_e_licencas.md)
- 📢 [Manual do Canal de Avisos](./docs/funcionalidades/04_avisos_e_comunicacao.md)

---

## 🔐 Segurança e Governança

Consulte a política de segurança em [SECURITY.md](SECURITY.md).
Nunca suba arquivos `.env`, certificados ou chaves privadas para o repositório.

---

## 📄 Licença

Propriedade exclusiva do **Centro de Desenvolvimento e Cidadania - CDC**. Consulte [LICENSE](LICENSE).
