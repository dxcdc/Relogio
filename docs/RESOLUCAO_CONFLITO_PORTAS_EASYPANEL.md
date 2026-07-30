# 🛠️ Resolução de Conflitos: Loop de Redirecionamento SSL & Portas no Easypanel (Traefik)

Este documento detalha o diagnóstico, causa raiz e solução de um problema altamente recorrente na infraestrutura corporativa do CDC: **Conflitos de portas (80/443) com o Easypanel (Traefik)** e o consequente **loop de redirecionamento infinito (ERR_TOO_MANY_REDIRECTS)** no Django.

---

## 🔍 1. O Problema Diagnósticado

Ao implantar novas aplicações na VPS Hostinger sob domínios oficiais (ex: `relogio.cdc.org.br`), dois sintomas ocorrem:
1. **Falha ao iniciar o Nginx:** O serviço Nginx do host falha em dar bind nas portas padrão `80` ou `443` com a mensagem:  
   `bind() to 0.0.0.0:80 failed (98: Address already in use)`.
2. **Loop de Redirecionamento no Navegador:** Após ajustar a porta do Nginx para uma porta secundária (ex: `8080`) e ativar o domínio, o navegador apresenta o erro `ERR_TOO_MANY_REDIRECTS` (redirecionamento infinito).

---

## ⚙️ 2. A Causa Raiz

### A. Conflito de Portas com o Traefik
A VPS Hostinger utiliza o **Easypanel** como painel de controle. O Easypanel implanta internamente o container **Traefik** como proxy de borda. 
- O Traefik está associado e escuta permanentemente nas portas externas **`80`** e **`443`** da VPS para gerenciar aplicações em containers.
- Logo, **o Nginx do host Linux não pode escutar nas portas 80/443**. Ele precisa operar em uma porta alternativa (como a **`8080`**).

```
[Cliente/Browser] ➔ HTTPS (443) ➔ [Traefik (Borda)] ➔ HTTP (8080) ➔ [Nginx (Host)] ➔ HTTP (8008) ➔ [Gunicorn (Django)]
```

### B. O Loop de Redirecionamento do Django (Redirect Loop)
Quando o Django está configurado para forçar conexões seguras com `SECURE_SSL_REDIRECT = True`:
1. O cliente se conecta por HTTPS (`https://relogio.cdc.org.br`) com o Traefik.
2. O Traefik descriptografa o SSL e repassa a requisição em texto plano (HTTP) para o Nginx na porta `8080`.
3. O Nginx por sua vez repassa em HTTP para o Gunicorn (Django) na porta `8008`.
4. O Django recebe a requisição. Como o Nginx repassou o tráfego via HTTP comum, o Django assume que o usuário está navegando sem segurança (HTTP).
5. O Django então responde com um redirecionamento `301 Moved Permanently` apontando para `https://relogio.cdc.org.br`.
6. O navegador recebe o redirecionamento e tenta carregar a página HTTPS de novo. O ciclo se repete infinitamente, travando a tela do usuário.

---

## 🛠️ 3. Como Resolver Passo a Passo

### Passo A: Ajustar a Porta de Comunicação do Nginx no Host
Configure o arquivo de site do Nginx (ex: `/etc/nginx/sites-available/relogio.cdc.org.br`) para escutar na porta **`8080`** (e não na 80/443):

```nginx
server {
    listen 8080;
    server_name relogio.cdc.org.br;
    ...
}
```

### Passo B: Informar ao Django que o SSL está Ativo (Ajuste de Cabeçalhos)
No mesmo arquivo de configuração do Nginx, configure o proxy reverso para forçar o cabeçalho **`X-Forwarded-Proto`** como **`https`**. Isso garante que o Django saiba que a requisição original do usuário veio via HTTPS:

```nginx
location / {
    proxy_pass http://127.0.0.1:8008;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    
    # 🚨 FORÇA O PROTOCOLO HTTPS (Resolve o loop de redirecionamento!)
    proxy_set_header X-Forwarded-Proto https;
}
```

E certifique-se de que a seguinte linha está ativa no `settings.py` do Django:
```python
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

### Passo C: Criar a Regra de Roteamento no Traefik (Easypanel)
Para que o Traefik da porta 443 saiba para onde enviar as requisições de `relogio.cdc.org.br`, crie uma regra de arquivo dinâmica em:  
`/etc/easypanel/traefik/config/relogio-custom.yaml`

Utilize o IP do gateway do Docker (**`172.16.0.1`**) apontando para a porta do Nginx (**`8080`**):

```yaml
http:
  routers:
    http-relogio-custom:
      entryPoints:
        - "http"
      priority: 100
      rule: "Host(`relogio.cdc.org.br`)"
      middlewares:
        - "redirect-to-https"
      service: "relogio-custom-service"
    https-relogio-custom:
      entryPoints:
        - "https"
      priority: 100
      rule: "Host(`relogio.cdc.org.br`)"
      service: "relogio-custom-service"
      tls:
        certResolver: "letsencrypt"
        domains:
          - main: "relogio.cdc.org.br"

  services:
    relogio-custom-service:
      loadBalancer:
        servers:
          - url: "http://172.16.0.1:8080"
```

Reinicie os serviços na VPS para aplicar:
```bash
systemctl restart nginx
systemctl restart relogio
```
