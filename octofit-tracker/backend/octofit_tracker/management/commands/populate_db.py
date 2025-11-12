"""
Django management command to populate the octofit_db database with test data.

Usage:
  python manage.py populate_db          # popula apenas se não houver dados
  python manage.py populate_db --force  # apaga dados existentes e popula novamente
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum
from datetime import datetime, timedelta
from octofit_tracker.models import User, Team, Activity, Leaderboard, Workout


class Command(BaseCommand):
    help = 'Populate the octofit_db database with test data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Apaga dados existentes antes de popular',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)

        if force:
            self.reset_data()
            self.create_demo_data()
        else:
            # se já houver usuários, não duplicar
            if User.objects.exists():
                self.stdout.write(
                    self.style.WARNING(
                        'Parece que já existem dados no banco. '
                        'Rode com --force para resetar e popular novamente.'
                    )
                )
                return

            self.create_demo_data()

    def reset_data(self):
        self.stdout.write('Removendo dados existentes (limpando M2M explicitamente)...')
        try:
            with transaction.atomic():
                # apagar activities primeiro (dependem de user)
                Activity.objects.all().delete()

                # limpar relações M2M de workouts antes de deletar (usar tabela through)
                try:
                    through_w = Workout.suggested_for.through
                    through_w.objects.all().delete()
                except Exception:
                    # fallback: tentar limpar via instâncias
                    for w in Workout.objects.all():
                        try:
                            w.suggested_for.clear()
                        except Exception:
                            pass
                # deletar workouts
                Workout.objects.all().delete()

                # deletar leaderboards
                Leaderboard.objects.all().delete()

                # limpar relações M2M de teams antes de deletar (usar tabela through)
                try:
                    through_t = Team.members.through
                    through_t.objects.all().delete()
                except Exception:
                    # fallback: tentar limpar via instâncias
                    for t in Team.objects.all():
                        try:
                            t.members.clear()
                        except Exception:
                            pass
                # deletar teams
                Team.objects.all().delete()

                # por fim, deletar usuários
                User.objects.all().delete()

            self.stdout.write(self.style.SUCCESS('Dados removidos com sucesso.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao remover dados: {e}'))
            raise

    def create_demo_data(self):
        self.stdout.write('Criando usuários...')
        users = []
        demo_users = [
            ('alice', 'alice@example.com', 'Alice', 'Silva'),
            ('bob', 'bob@example.com', 'Bob', 'Souza'),
            ('carol', 'carol@example.com', 'Carol', 'Lima'),
            ('dave', 'dave@example.com', 'Dave', 'Oliveira'),
        ]

        for username, email, first, last in demo_users:
            u = User.objects.create(
                username=username,
                email=email,
                first_name=first,
                last_name=last,
            )
            users.append(u)

        self.stdout.write('Criando times e atribuindo membros...')
        team1 = Team.objects.create(name='Team Alpha')
        team2 = Team.objects.create(name='Team Beta')
        team1.members.add(users[0], users[1])
        team2.members.add(users[2], users[3])

        self.stdout.write('Criando workouts sugeridos...')
        w1 = Workout.objects.create(
            name='Quick HIIT',
            description='20-minute high intensity interval training',
        )
        w2 = Workout.objects.create(
            name='Morning Yoga',
            description='30-minute mobility and stretch flow',
        )
        w3 = Workout.objects.create(
            name='Long Run',
            description='60-minute steady state run',
        )
        # sugerir workouts para usuários
        w1.suggested_for.add(users[0], users[2])
        w2.suggested_for.add(users[1], users[3])
        w3.suggested_for.add(*users)

        self.stdout.write('Criando atividades (historico)...')
        base_date = datetime.now()
        for i, u in enumerate(users):
            # criar algumas atividades por usuário
            for j in range(3):
                act_date = base_date - timedelta(days=i * 2 + j)
                duration = 20 + i * 10 + j * 5
                calories = float(150 + i * 30 + j * 20)
                Activity.objects.create(
                    user=u,
                    activity_type='run' if j % 2 == 0 else 'bike',
                    duration=duration,
                    calories_burned=calories,
                    date=act_date,
                )

        self.stdout.write('Calculando leaderboards por time...')
        # calcular pontos como soma de calories (arredondada) dos membros
        for team in Team.objects.all():
            members = team.members.all()
            total_points = 0
            for m in members:
                agg = Activity.objects.filter(user=m).aggregate(total=Sum('calories_burned'))
                total_points += int(agg['total'] or 0)
            Leaderboard.objects.create(team=team, total_points=total_points)

        self.stdout.write(
            self.style.SUCCESS('População de dados de teste concluída.')
        )
