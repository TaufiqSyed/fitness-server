from django.contrib import admin
from .models import (
    UserProfile, DietLogItem, Exercise, Workout, WorkoutExercise,
    WorkoutProgram, ActiveWorkoutProgram, ProgramDay, LoggedWorkout, LoggedExercise
)

admin.site.register(UserProfile)
admin.site.register(DietLogItem)
admin.site.register(Exercise)
admin.site.register(Workout)
admin.site.register(WorkoutExercise)
admin.site.register(WorkoutProgram)
admin.site.register(ProgramDay)
admin.site.register(LoggedWorkout)
admin.site.register(LoggedExercise)
admin.site.register(ActiveWorkoutProgram)