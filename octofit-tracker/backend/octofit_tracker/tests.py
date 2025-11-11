from django.test import TestCase
from .models import User, Team, Activity, Leaderboard, Workout

class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create(username='testuser', email='test@example.com', first_name='Test', last_name='User')
        self.assertEqual(user.username, 'testuser')

class TeamModelTest(TestCase):
    def test_create_team(self):
        user = User.objects.create(username='testuser', email='test@example.com', first_name='Test', last_name='User')
        team = Team.objects.create(name='Team A')
        team.members.add(user)
        self.assertIn(user, team.members.all())

class ActivityModelTest(TestCase):
    def test_create_activity(self):
        user = User.objects.create(username='testuser', email='test@example.com', first_name='Test', last_name='User')
        activity = Activity.objects.create(user=user, activity_type='Run', duration=30, calories_burned=300)
        self.assertEqual(activity.activity_type, 'Run')

class LeaderboardModelTest(TestCase):
    def test_create_leaderboard(self):
        team = Team.objects.create(name='Team A')
        leaderboard = Leaderboard.objects.create(team=team, total_points=100)
        self.assertEqual(leaderboard.total_points, 100)

class WorkoutModelTest(TestCase):
    def test_create_workout(self):
        workout = Workout.objects.create(name='Cardio', description='Cardio workout')
        self.assertEqual(workout.name, 'Cardio')
