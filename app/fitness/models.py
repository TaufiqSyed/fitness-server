from django.conf import settings
from django.db import models
from django.utils import timezone
from .user_manager import UserProfile

class DietLogItem(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    food_name = models.TextField()
    image = models.ImageField(upload_to='diet_log_images/', null=True, blank=True)  # Image field for uploads
    food_calories = models.IntegerField()
    protein_grams = models.FloatField()
    carbs_grams = models.FloatField()
    fat_grams = models.FloatField()
    log_time = models.DateTimeField()

    def __str__(self):
        return f"{self.user} - {self.log_time}"



class Exercise(models.Model):
    body_part = models.CharField(max_length=100)
    equipment = models.CharField(max_length=100)
    gif_url = models.URLField(max_length=200)
    exercise_id = models.CharField(max_length=100, unique=True, primary_key=True)
    name = models.CharField(max_length=100)
    target = models.CharField(max_length=100)
    calories_burned = models.FloatField(default=200)
    
    # Store list data as semicolon-separated strings
    secondary_muscles = models.TextField()
    instructions = models.TextField()

    def set_secondary_muscles(self, muscles_list):
        self.secondary_muscles = ';'.join(muscles_list)

    def get_secondary_muscles(self):
        return self.secondary_muscles.split(';') if self.secondary_muscles else []

    def set_instructions(self, instructions_list):
        self.instructions = ';'.join(instructions_list)

    def get_instructions(self):
        return self.instructions.split(';') if self.instructions else []
    
    def __str__(self):
        return self.name

class Workout(models.Model):
    name = models.CharField(max_length=100)
    image_url = models.URLField(max_length=200)
    description = models.TextField()
    body_part = models.CharField(max_length=100)
    exercises = models.ManyToManyField(Exercise, through='WorkoutExercise')

class FeaturedWorkout(models.Model):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE)
    date = models.DateField()

class WorkoutExercise(models.Model):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    order = models.IntegerField(default=1)
    sets = models.IntegerField(default=1)
    reps = models.IntegerField(default=1)
    weight_in_kg = models.FloatField(null=True, blank=True)
    km_ran = models.FloatField(null=True, blank=True)

class WorkoutProgram(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField()

class ProgramDay(models.Model):
    workout_program = models.ForeignKey(WorkoutProgram, related_name='days', on_delete=models.CASCADE)
    workout = models.ForeignKey(Workout, on_delete=models.SET_NULL, null=True, blank=True)
    day_of_week = models.IntegerField()

class LoggedWorkout(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    workout_name = models.CharField(max_length=100)
    duration_minutes = models.FloatField()
    log_time = models.DateTimeField()


class LoggedExercise(models.Model):
    logged_workout = models.ForeignKey(LoggedWorkout, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    order = models.IntegerField()
    sets_completed = models.IntegerField()
    reps_completed = models.IntegerField()
    weight_used_kg = models.FloatField(null=True, blank=True)
    km_ran = models.FloatField(null=True, blank=True)


class ActiveWorkoutProgram(models.Model):
    workout_program = models.ForeignKey(WorkoutProgram, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
