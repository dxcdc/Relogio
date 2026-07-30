# 🚀 Guia de Deploy no VPS Hostinger — `relogio.cdc.org.br`

Este guia fornece o passo a passo simplificado para realizar o deploy em produção da aplicação **CDC Relógio** na VPS da Hostinger com suporte a SSL gratuito (Let's Encrypt).

---

## 📌 Passos Prévios (Configuração do Domínio no DNS)

Antes de rodar o comando no servidor, configure o registro DNS da zona `cdc.org.br`:

| Tipo | Nome / Host | Valor / Apontamento |
| :--- | :--- | :--- |
| **A** | `relogio` | `IP_DA_SUA_VPS_HOSTINGER` |

---

## ⚡ Comandos para Executar no Terminal da VPS Hostinger (SSH)

Conecte no terminal da sua VPS Hostinger via SSH:

```bash
ssh root@IP_DA_SUA_VPS_HOSTINGER
```

Em seguida, **execute apenas este único comando abaixo** para baixar e rodar a instalação automatizada:

```bash
curl -sSL https://raw.githubusercontent.com/dxcdc/Relogio/main/deploy/setup_vps.sh | bash
```

---

## 🔍 O que o script de automação faz sozinho:

1. **Instala o Nginx, Python 3, Git e Certbot SSL.**
2. **Clona o repositório oficial `https://github.com/dxcdc/Relogio.git`.**
3. **Cria o ambiente virtual Python (`venv`) e instala todas as dependências (`requirements.txt` + `gunicorn`).**
4. **Gera a chave secreta de produção (`DJANGO_SECRET_KEY`) e configura o arquivo `.env`.**
5. **Executa a criação de tabelas no banco de dados (`migrate`) e coleta estáticos (`collectstatic`).**
6. **Configura o serviço Gunicorn no Systemd (`systemctl enable relogio`).**
7. **Configura o Nginx com Proxy Reverso para o socket UNIX.**
8. **Emite e instala automaticamente o Certificado SSL HTTPS Gratuito via Let's Encrypt.**

---

## 🌐 Acesso Pós-Deploy

Após o término da instalação, a aplicação estará online e segura no endereço oficial:

👉 **[https://relogio.cdc.org.br](https://relogio.cdc.org.br)**

---

## 🔄 Como Atualizar a Aplicação no Futuro (Deploy Contínuo)

Quando fizer novas alterações no código e enviar para o GitHub, basta rodar este comando no terminal SSH da VPS:

```bash
cd /var/www/relogio && git pull origin main && ./venv/bin/python manage.py migrate --noinput && ./venv/bin/python manage.py collectstatic --noinput && systemctl restart relogio nginx
```
