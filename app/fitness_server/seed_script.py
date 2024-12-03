import json
from fitness.models import (
    UserProfile, DietLogItem, Workout, WorkoutExercise, WorkoutProgram, ProgramDay,
    LoggedWorkout, LoggedExercise, ActiveWorkoutProgram, Exercise, FeaturedWorkout
)
from fitness.serializers import ExerciseSerializer
from django.utils import timezone

# Seed Exercises
def seed_exercises():
    print('Seeding exercises...')
    with open('fitness_server/seed_exercise.json') as f:
        exercises_data = json.load(f)

    for exercise_data in exercises_data:
        exercise_data['exercise_id'] = exercise_data.pop('id')
        exercise_data['gif_url'] = exercise_data.pop('gifUrl')
        exercise_data['body_part'] = exercise_data.pop('bodyPart')

        exercise_data['secondaryMuscles'] = exercise_data.pop('secondaryMuscles', [])
        exercise_data['instructions'] = exercise_data.pop('instructions', [])
        exercise_data['calories_burned'] = 200

        serializer = ExerciseSerializer(data=exercise_data)
        if serializer.is_valid():
            serializer.save()
            print(f'Successfully added exercise: {exercise_data["name"]}')
        else:
            print(f'Failed to add exercise: {exercise_data["name"]}. Errors: {serializer.errors}')

# Seed UserProfile
def seed_user_profiles():
    user_profiles = [
        {
            "email": "user1@example.com",
            "height_cm": 175,
            "weight_kg": 70,
            "target_weight_kg": 65,
            "age": 30,
            "activity_level": "Moderately active",
            "gender": "Male",
            "password": "securepassword1"
        },
        {
            "email": "user2@example.com",
            "height_cm": 160,
            "weight_kg": 60,
            "target_weight_kg": 55,
            "age": 25,
            "activity_level": "Lightly active",
            "gender": "Female",
            "password": "securepassword2"
        },
    ]

    for profile in user_profiles:
        user = UserProfile(
            email=profile["email"],
            height_cm=profile["height_cm"],
            weight_kg=profile["weight_kg"],
            target_weight_kg=profile["target_weight_kg"],
            age=profile["age"],
            activity_level=profile["activity_level"],
            gender=profile["gender"]
        )
        user.set_password(profile["password"])
        user.save()
        print(f'Successfully added user profile: {user.email}')

# Seed DietLogItem
def seed_diet_log_items():
    diet_log_items = [
        {
            "user": UserProfile.objects.get(email="user1@example.com"),
            "food_calories": 500,
            "protein_grams": 25,
            "carbs_grams": 50,
            "fat_grams": 15,
            "log_time": timezone.now()
        },
        {
            "user": UserProfile.objects.get(email="user2@example.com"),
            "food_calories": 300,
            "protein_grams": 20,
            "carbs_grams": 30,
            "fat_grams": 10,
            "log_time": timezone.now()
        },
    ]

    for item in diet_log_items:
        log_item = DietLogItem(
            user=item["user"],
            food_calories=item["food_calories"],
            protein_grams=item["protein_grams"],
            carbs_grams=item["carbs_grams"],
            fat_grams=item["fat_grams"],
            log_time=item["log_time"]
        )
        log_item.save()
        print(f'Successfully added diet log item for user: {log_item.user.email}')

# Seed Workouts and WorkoutExercises
def seed_workouts_and_exercises():
    exercises = Exercise.objects.all()

    workout1 = Workout.objects.create(
        name="Full Body Workout",
        description="A comprehensive workout targeting all major muscle groups."
    )

    workout2 = Workout.objects.create(
        name="Cardio Blast",
        description="High-intensity cardio workout for endurance."
    )

    for i in range(3):
        WorkoutExercise.objects.create(
            workout=workout1,
            exercise=exercises[i],
            order=i+1,
            sets=3,
            reps=10,
            weight_in_kg=20
        )

    for i in range(3, 6):
        WorkoutExercise.objects.create(
            workout=workout2,
            exercise=exercises[i],
            order=i-2,
            sets=2,
            reps=15
        )

    print(f'Successfully added workouts and linked exercises.')

# Seed WorkoutProgram and ProgramDay
def seed_workout_programs():
    workout_program = WorkoutProgram.objects.create(
        user=UserProfile.objects.get(email="user1@example.com"),
        name="Beginner Fitness Program",
        description="A program designed for beginners to build strength and endurance."
    )

    ProgramDay.objects.create(workout_program=workout_program, workout=Workout.objects.get(name="Full Body Workout"), day_of_week=1)
    ProgramDay.objects.create(workout_program=workout_program, workout=Workout.objects.get(name="Cardio Blast"), day_of_week=3)

# Seed LoggedWorkout and LoggedExercise
def seed_logged_workouts():
    user = UserProfile.objects.get(email="user1@example.com")
    
    logged_workout = LoggedWorkout.objects.create(
        user=user,
        workout_name="Full Body Workout",
        duration_minutes=45,
        log_time=timezone.now()
    )

    exercises = Exercise.objects.all()
    for i, exercise in enumerate(exercises[:3], start=1):
        LoggedExercise.objects.create(
            logged_workout=logged_workout,
            exercise=exercise,
            order=i,
            sets_completed=3,
            reps_completed=10,
            weight_used_kg=20 if exercise.name != "Running" else None,
            km_ran=2.5 if exercise.name == "Running" else None
        )
    print(f'Successfully logged workout and exercises for user: {user.email}')

# Seed ActiveWorkoutProgram
def seed_active_workout_program():
    user = UserProfile.objects.get(email="user1@example.com")
    workout_program = WorkoutProgram.objects.first()
    
    ActiveWorkoutProgram.objects.create(
        workout_program=workout_program,
        user=user,
        start_date=timezone.now(),
        end_date=timezone.now() + timezone.timedelta(days=30),
        is_active=True
    )

# Seed FeaturedWorkouts
def seed_featured_workouts():
    print('Seeding featured workouts...')
    workout = Workout.objects.first()
    if not workout:
        print("No workouts available to feature. Skipping FeaturedWorkout seeding.")
        return

    featured_workouts = [
        {"workout": workout, "date": timezone.now().date()},
        {"workout": workout, "date": (timezone.now() + timezone.timedelta(days=1)).date()},
    ]

    for fw in featured_workouts:
        FeaturedWorkout.objects.create(workout=fw["workout"], date=fw["date"])
        print(f"Successfully added featured workout for date: {fw['date']}")

# Seed DietLogItem
def seed_diet_log_items():
    print('Seeding diet log items...')
    diet_log_items = [
        {
            "user": UserProfile.objects.get(email="user1@example.com"),
            "food_name": "Grilled Chicken Salad",
            "food_calories": 400,
            "protein_grams": 35,
            "carbs_grams": 20,
            "fat_grams": 15,
            "log_time": timezone.now()
        },
        {
            "user": UserProfile.objects.get(email="user2@example.com"),
            "food_name": "Avocado Toast",
            "food_calories": 300,
            "protein_grams": 10,
            "carbs_grams": 40,
            "fat_grams": 15,
            "log_time": timezone.now()
        },
    ]

    for item in diet_log_items:
        log_item = DietLogItem(
            user=item["user"],
            food_name=item["food_name"],
            food_calories=item["food_calories"],
            protein_grams=item["protein_grams"],
            carbs_grams=item["carbs_grams"],
            fat_grams=item["fat_grams"],
            log_time=item["log_time"]
        )
        log_item.save()
        print(f"Successfully added diet log item for user: {log_item.user.email}")

# Main function to run all seeds
def run_seeds():
    seed_exercises()
    seed_user_profiles()
    seed_diet_log_items()
    seed_workouts_and_exercises()
    seed_workout_programs()
    seed_logged_workouts()
    seed_active_workout_program()

    seed_diet_log_items()
    seed_featured_workouts()

run_seeds()
