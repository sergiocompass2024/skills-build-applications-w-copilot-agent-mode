mode: 'agent'
model: GPT-4.1

# Django App Updates

- All Django project files are em `octofit-tracker/backend/octofit_tracker`.

1. Atualize o `settings.py` para conexão com MongoDB e CORS.
2. Atualize `models.py`, `serializers.py`, `urls.py`, `views.py`, `tests.py` e `admin.py` para suportar as coleções de usuários, equipes, atividades, leaderboard e treinos.
3. Garanta que `/` aponte para a API e que `api_root` esteja presente em `urls.py`. (Veja <attachments> acima para conteúdos dos arquivos. Você pode não precisar buscar ou ler o arquivo novamente.)
