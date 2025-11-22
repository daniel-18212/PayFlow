# Contas a Pagar

Sistema web simples, moderno e robusto para controle de contas a pagar, feito em Django.

## ✨ Funcionalidades
- Cadastro de contas à vista e parceladas
- Dashboard financeiro com totais (em dia, vencido, quitado)
- Filtros avançados e busca rápida
- Paginação automática
- Cadastro de categorias
- Status colorido e intuitivo
- Ações rápidas (quitar, reabrir, excluir)
- Bloqueio de edição/exclusão de contas quitadas
- Reabertura de conta apenas por superusuário
- Mensagens toast de feedback
- Interface responsiva e amigável
- Validações rígidas e feedback visual
- Login, logout e proteção de acesso

## 🚀 Como rodar localmente

1. **Clone o repositório:**
   ```bash
   git clone <url-do-repositorio>
   cd contas-a-pagar
   ```
2. **Crie o ambiente virtual e instale as dependências:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Aplique as migrações:**
   ```bash
   python manage.py migrate
   ```
4. **Crie um superusuário:**
   ```bash
   python manage.py createsuperuser
   ```
5. **Inicie o servidor:**
   ```bash
   python manage.py runserver
   ```
6. **Acesse:**
   - Sistema: [http://localhost:8000/contas/](http://localhost:8000/contas/)
   - Admin: [http://localhost:8000/admin/](http://localhost:8000/admin/)

## 📝 Requisitos
- Python 3.10+
- Django 5+
- Bootstrap 5 (já incluso via CDN)

## 💡 Dicas de uso
- O sistema é autoexplicativo e à prova de erros.
- Campos obrigatórios são destacados.
- Contas quitadas não podem ser editadas/excluídas.
- Use o dashboard para ter visão rápida das finanças.
- Utilize a busca e filtros para localizar contas facilmente.

## 📦 Estrutura do projeto
- `contas/` — app principal (modelos, views, forms, templates)
- `contas_a_pagar/` — configurações do projeto Django
- `staticfiles/` — arquivos estáticos coletados
- `templates/` — base e páginas do sistema
- `requirements.txt` — dependências do projeto
- `manage.py` — utilitário Django

## 🔒 Segurança
- Senhas protegidas por hash (Django padrão)
- Proteção CSRF e XSS nativa
- Apenas usuários autenticados acessam o sistema

## 👨‍💻 Autor e contato
- Desenvolvido por Daniel
- Dúvidas/sugestões: abra uma issue ou envie um e-mail

---
Sistema pensado para ser simples, elegante e fácil para qualquer usuário! 