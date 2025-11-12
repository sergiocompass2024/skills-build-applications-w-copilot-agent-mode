#!/usr/bin/env python3
"""
Script para popular o banco de dados do projeto Octofit Tracker com dados de teste.

Uso:
  python populate_db.py         # popula apenas se não houver dados
  python populate_db.py --force # apaga dados existentes e popula novamente

O script configura o ambiente Django automaticamente.
"""
import os
import sys
import argparse
from datetime import datetime, timedelta
import traceback
from django.db import transaction


def setup_django():
    # Adiciona o diretório do backend ao path para permitir importar o pacote do projeto
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)

    # Para permitir rodar o script sem depender do MongoDB/djongo local,
    # preferimos usar um settings alternativo que aponta para sqlite quando
    # a variável de ambiente POPULATE_USE_SQLITE estiver definida.
    if os.environ.get('POPULATE_USE_SQLITE'):
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'temp_settings_for_populate')
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'octofit_tracker.settings')
    try:
        import django
        django.setup()
    except Exception as e:
        print('Erro ao configurar Django:', e)
        raise


def reset_data(models):
    print('Removendo dados existentes (limpando M2M explicitamente)...')
    try:
        with transaction.atomic():
            # apagar activities primeiro (dependem de user)
            models.Activity.objects.all().delete()

            # limpar relações M2M de workouts antes de deletar (usar tabela through para evitar instâncias sem PK)
            try:
                through_w = models.Workout.suggested_for.through
                through_w.objects.all().delete()
            except Exception:
                # fallback: tentar limpar via instâncias (pode falhar se houver instâncias sem PK)
                for w in models.Workout.objects.all():
                    try:
                        w.suggested_for.clear()
                    except Exception:
                        pass
            # deletar workouts
            models.Workout.objects.all().delete()

            # deletar leaderboards
            models.Leaderboard.objects.all().delete()

            # limpar relações M2M de teams antes de deletar (usar tabela through para evitar instâncias sem PK)
            try:
                through_t = models.Team.members.through
                through_t.objects.all().delete()
            except Exception:
                # fallback: tentar limpar via instâncias
                for t in models.Team.objects.all():
                    try:
                        t.members.clear()
                    except Exception:
                        pass
            # deletar teams
            models.Team.objects.all().delete()

            # por fim, deletar usuários
            models.User.objects.all().delete()

        print('Dados removidos com sucesso.')
    except Exception:
        print('Erro ao remover dados — traceback abaixo:')
        traceback.print_exc()
        raise


def create_demo_data(models):
    print('Criando usuários...')
    users = []
    demo_users = [
        ('alice', 'alice@example.com', 'Alice', 'Silva'),
        ('bob', 'bob@example.com', 'Bob', 'Souza'),
        ('carol', 'carol@example.com', 'Carol', 'Lima'),
        ('dave', 'dave@example.com', 'Dave', 'Oliveira'),
    ]

    for username, email, first, last in demo_users:
        u = models.User.objects.create(username=username, email=email, first_name=first, last_name=last)
        users.append(u)

    print('Criando times e atribuindo membros...')
    team1 = models.Team.objects.create(name='Team Alpha')
    team2 = models.Team.objects.create(name='Team Beta')
    team1.members.add(users[0], users[1])
    team2.members.add(users[2], users[3])

    print('Criando workouts sugeridos...')
    w1 = models.Workout.objects.create(name='Quick HIIT', description='20-minute high intensity interval training')
    w2 = models.Workout.objects.create(name='Morning Yoga', description='30-minute mobility and stretch flow')
    w3 = models.Workout.objects.create(name='Long Run', description='60-minute steady state run')
    # sugerir workouts para usuários
    w1.suggested_for.add(users[0], users[2])
    w2.suggested_for.add(users[1], users[3])
    w3.suggested_for.add(*users)

    print('Criando atividades (historico)...')
    base_date = datetime.now()
    for i, u in enumerate(users):
        # criar algumas atividades por usuário
        for j in range(3):
            act_date = base_date - timedelta(days=i*2 + j)
            duration = 20 + i*10 + j*5
            calories = float(150 + i*30 + j*20)
            models.Activity.objects.create(user=u, activity_type='run' if j % 2 == 0 else 'bike', duration=duration, calories_burned=calories, date=act_date)

    print('Calculando leaderboards por time...')
    # calcular pontos como soma de calories (arredondada) dos membros
    for team in models.Team.objects.all():
        members = team.members.all()
        total_points = 0
        for m in members:
            total_points += int(models.Activity.objects.filter(user=m).aggregate(models.models.Sum('calories_burned'))['calories_burned__sum'] or 0)
        lb = models.Leaderboard.objects.create(team=team, total_points=total_points)

    print('População de dados de teste concluída.')


def main():
    parser = argparse.ArgumentParser(description='Popula o banco com dados de teste para Octofit Tracker')
    parser.add_argument('--force', action='store_true', help='Apaga dados existentes antes de popular')
    args = parser.parse_args()

    setup_django()

    # importa modelos do app
    try:
        from octofit_tracker import models
    except Exception as e:
        print('Erro ao importar models do app octofit_tracker:', e)
        raise

    if args.force:
        reset_data(models)
        create_demo_data(models)
    else:
        # se já houver usuários, não duplicar
        if models.User.objects.exists():
            print('Parece que já existem dados no banco. Rode com --force para resetar e popular novamente.')
            return
        create_demo_data(models)


if __name__ == '__main__':
    main()
