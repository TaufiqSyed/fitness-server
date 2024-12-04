import datetime
from django.test import TestCase
from django.utils.timezone import now
from .models import (
    DietLogItem, Exercise, Workout, FeaturedWorkout, WorkoutExercise,
    WorkoutProgram, ProgramDay, LoggedWorkout, LoggedExercise, ActiveWorkoutProgram
)
from .user_manager import UserProfile


class ModelsTestCase(TestCase):
    def setUp(self):
        # Set up data for all tests
        self.user = UserProfile.objects.create(email="testuser@example.com")
        self.exercise = Exercise.objects.create(
            body_part="legs",
            equipment="dumbbell",
            gif_url="http://example.com/exercise.gif",
            exercise_id="ex1",
            name="Squat",
            target="quads",
            calories_burned=300,
            secondary_muscles="hamstrings;glutes",
            instructions="stand;lift;squat"
        )
        self.workout = Workout.objects.create(
            name="Leg Day",
            image_url="http://example.com/workout.jpg",
            description="Workout for legs",
            body_part="legs"
        )
        self.workout_program = WorkoutProgram.objects.create(
            user=self.user,
            name="Summer Shred",
            description="A program for summer"
        )
        self.logged_workout = LoggedWorkout.objects.create(
            user=self.user,
            workout_name="Morning Workout",
            duration_minutes=45,
            log_time=now()
        )

    # Test DietLogItem model
    def test_diet_log_item_str(self):
        diet_log_item = DietLogItem.objects.create(
            user=self.user,
            food_name="Apple",
            food_calories=95,
            protein_grams=0.3,
            carbs_grams=25,
            fat_grams=0.2,
            log_time=now()
        )
        self.assertEqual(str(diet_log_item), f"{self.user} - {diet_log_item.log_time}")

    # Test Exercise model
    def test_exercise_str(self):
        self.assertEqual(str(self.exercise), "Squat")

    def test_exercise_secondary_muscles(self):
        muscles = self.exercise.get_secondary_muscles()
        self.assertListEqual(muscles, ["hamstrings", "glutes"])

        self.exercise.set_secondary_muscles(["calves", "hamstrings"])
        self.assertEqual(self.exercise.secondary_muscles, "calves;hamstrings")

    def test_exercise_instructions(self):
        instructions = self.exercise.get_instructions()
        self.assertListEqual(instructions, ["stand", "lift", "squat"])

        self.exercise.set_instructions(["step1", "step2"])
        self.assertEqual(self.exercise.instructions, "step1;step2")

    # Test Workout model
    def test_workout_creation(self):
        self.assertEqual(self.workout.name, "Leg Day")

    # Test FeaturedWorkout model
    def test_featured_workout_creation(self):
        featured_workout = FeaturedWorkout.objects.create(
            workout=self.workout,
            date=datetime.date.today()
        )
        self.assertEqual(featured_workout.workout, self.workout)

    # Test WorkoutExercise model
    def test_workout_exercise_creation(self):
        workout_exercise = WorkoutExercise.objects.create(
            workout=self.workout,
            exercise=self.exercise,
            order=1,
            sets=3,
            reps=12,
            weight_in_kg=20.0
        )
        self.assertEqual(workout_exercise.sets, 3)

    # Test WorkoutProgram model
    def test_workout_program_creation(self):
        self.assertEqual(self.workout_program.name, "Summer Shred")

    # Test ProgramDay model
    def test_program_day_creation(self):
        program_day = ProgramDay.objects.create(
            workout_program=self.workout_program,
            workout=self.workout,
            day_of_week=1
        )
        self.assertEqual(program_day.day_of_week, 1)

    # Test LoggedWorkout model
    def test_logged_workout_creation(self):
        self.assertEqual(self.logged_workout.duration_minutes, 45)

    # Test LoggedExercise model
    def test_logged_exercise_creation(self):
        logged_exercise = LoggedExercise.objects.create(
            logged_workout=self.logged_workout,
            exercise=self.exercise,
            order=1,
            sets_completed=3,
            reps_completed=12,
            weight_used_kg=20.0
        )
        self.assertEqual(logged_exercise.sets_completed, 3)

    # Test ActiveWorkoutProgram model
    def test_active_workout_program_creation(self):
        active_program = ActiveWorkoutProgram.objects.create(
            workout_program=self.workout_program,
            user=self.user,
            start_date=now(),
            end_date=now() + datetime.timedelta(days=30),
            is_active=True
        )
        self.assertTrue(active_program.is_active)
