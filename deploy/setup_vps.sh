#!/bin/bash
set -e

echo "🚀 Iniciando Instalação do CDC Relógio em relogio.cdc.org.br..."

# 1. Atualiza sistema
apt update && apt upgrade -y
apt install -y python3 python3-venv python3-pip python3-dev build-essential pkg-config default-libmysqlclient-dev nginx git certbot python3-certbot-nginx

# 2. Cria pasta do projeto se não existir
mkdir -p /var/www/relogio
cd /var/www/relogio

# 3. Clona repositório se a pasta estiver vazia
if [ ! -d "/var/www/relogio/.git" ]; then
    echo "📦 Clonando o repositório..."
    git clone https://github.com/dxcdc/Relogio.git /var/www/relogio
fi

# 4. Ambiente Virtual Python
echo "🐍 Configurando Python e Dependências..."
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
./venv/bin/pip install gunicorn

# 5. Configuração do .env de Produção
if [ ! -f "/var/www/relogio/.env" ]; then
    echo "⚙️ Gerando arquivo .env de produção..."
    SECRET_KEY=$(./venv/bin/python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    cat <<EOF > /var/www/relogio/.env
DJANGO_SECRET_KEY=${SECRET_KEY}
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=relogio.cdc.org.br,localhost,127.0.0.1
RESEND_TEST_EMAIL=rh@cdc.org.br
EOF
fi

# 6. Migrações e Coleta de Estáticos
echo "🗄️ Executando migrações do banco e estáticos..."
mkdir -p /var/www/relogio/logs
./venv/bin/python manage.py migrate --noinput
./venv/bin/python manage.py collectstatic --noinput

# 7. Configura Serviço Systemd (Gunicorn)
echo "⚙️ Configurando serviço Systemd..."
cp deploy/systemd/relogio.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable relogio
systemctl restart relogio

# 8. Configura Nginx
echo "🌐 Configurando Nginx Web Server..."
cp deploy/nginx/relogio.cdc.org.br.conf /etc/nginx/sites-available/relogio.cdc.org.br
ln -sf /etc/nginx/sites-available/relogio.cdc.org.br /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

# 9. SSL com Certbot (Let's Encrypt)
echo "🔒 Solicitando Certificado SSL Let's Encrypt para relogio.cdc.org.br..."
certbot --nginx -d relogio.cdc.org.br --non-interactive --agree-tos -m rh@cdc.org.br --redirect || echo "⚠️ Certbot falhou. Verifique se o IP no DNS relogio.cdc.org.br já propagou."

echo "✅ Deploy concluído com sucesso!"
echo "🌐 Acesse no seu navegador: https://relogio.cdc.org.br"
