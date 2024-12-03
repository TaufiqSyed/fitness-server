# core/serializers.py
from rest_framework import serializers
from .models import *

from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password', 'height_cm', 'gender', 'weight_kg', 'target_weight_kg', 'age', 'activity_level']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password'])  # Hash the password
        user.save()
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

class DietLogItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DietLogItem
        fields = ['id', 'image', 'food_calories', 'food_name', 'protein_grams', 'carbs_grams', 'fat_grams', 'log_time']
        read_only_fields = ['user']  # Mark user as read-only

# class ExerciseSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Exercise
#         fields = '__all__'


class ExerciseSerializer(serializers.ModelSerializer):
    secondaryMuscles = serializers.ListField(
        child=serializers.CharField(), source='get_secondary_muscles', write_only=False
    )
    instructions = serializers.ListField(
        child=serializers.CharField(), source='get_instructions', write_only=False
    )

    class Meta:
        model = Exercise
        fields = ['body_part', 'equipment', 'gif_url', 'exercise_id', 'name', 'target', 'secondaryMuscles', 'instructions', 'calories_burned']
        
    def create(self, validated_data):
        # Process list fields to semicolon-separated strings
        secondary_muscles = validated_data.pop('get_secondary_muscles', [])
        instructions = validated_data.pop('get_instructions', [])
        
        exercise = Exercise(**validated_data)
        exercise.set_secondary_muscles(secondary_muscles)
        exercise.set_instructions(instructions)
        exercise.save()
        return exercise
    
    def update(self, instance, validated_data):
        secondary_muscles = validated_data.pop('get_secondary_muscles', None)
        instructions = validated_data.pop('get_instructions', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if secondary_muscles is not None:
            instance.set_secondary_muscles(secondary_muscles)
        if instructions is not None:
            instance.set_instructions(instructions)
        
        instance.save()
        return instance

class WorkoutExerciseSerializer(serializers.ModelSerializer):
    exercise_id = serializers.PrimaryKeyRelatedField(source='exercise.exercise_id', read_only=True)
    name = serializers.CharField(source='exercise.name', read_only=True)

    class Meta:
        model = WorkoutExercise
        fields = ['exercise_id', 'name', 'order', 'sets', 'reps', 'weight_in_kg', 'km_ran']

class WorkoutSerializer(serializers.ModelSerializer):
    exercises = WorkoutExerciseSerializer(many=True, read_only=True, source='workoutexercise_set')
    class Meta:
        model = Workout
        fields = '__all__'

# class ProgramDaySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ProgramDay
#         fields = '__all__'
class ProgramDaySerializer(serializers.ModelSerializer):
    workout = WorkoutSerializer(read_only=True)  # Use WorkoutSerializer to populate workout details

    class Meta:
        model = ProgramDay
        fields = ['id', 'day_of_week', 'workout']  # Exclude workout_program_id

class WorkoutProgramSerializer(serializers.ModelSerializer):
    days = ProgramDaySerializer(many=True, read_only=True)
    class Meta:
        model = WorkoutProgram
        fields = '__all__'

class LoggedExerciseSerializer(serializers.ModelSerializer):
    exercise_id = serializers.IntegerField(source="exercise.exercise_id", read_only=True)
    name = serializers.CharField(source="exercise.name", read_only=True)

    class Meta:
        model = LoggedExercise
        fields = ['exercise_id', 'name', 'order', 'sets_completed', 'reps_completed', 'weight_used_kg', 'km_ran']


class LoggedWorkoutSerializer(serializers.ModelSerializer):
    exercises = LoggedExerciseSerializer(many=True, source='loggedexercise_set', read_only=True)

    class Meta:
        model = LoggedWorkout
        fields = ['id', 'user', 'workout_name', 'duration_minutes', 'log_time', 'exercises']
        read_only_fields = ['user']

class ActiveWorkoutProgramSerializer(serializers.ModelSerializer):
    workout_program = WorkoutProgramSerializer()
    days = ProgramDaySerializer(many=True, source='workout_program.days')

    class Meta:
        model = ActiveWorkoutProgram
        fields = ['id', 'workout_program', 'start_date', 'end_date', 'is_active', 'days']
