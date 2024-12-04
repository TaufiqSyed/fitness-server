# core/views.py
from rest_framework import permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from datetime import datetime, timedelta
from django.db.models import Sum

from django.utils import timezone
from datetime import date, datetime, timedelta
from .models import *
from .serializers import *
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from django.db.models import Prefetch
import openai
from .utils.gpt_food_scanner import GPTFoodScanner
from .utils.get_current_day import get_current_day
from django.shortcuts import get_object_or_404
import os 
from django.db.models import Q
from django.utils.timezone import now
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

# class UserSignupView(APIView):
#     def post(self, request):
#         serializer = UserSignupSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.save()
#             return Response({'email': user.email}, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this endpoint

    def get(self, request):
        """Retrieve the authenticated user's profile."""
        user = request.user  # The currently authenticated user
        serializer = UserSignupSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        """Update the authenticated user's profile."""
        user = request.user  # The currently authenticated user
        data = request.data

        # Exclude `email` and `password` from being updated
        for field in ['email', 'password']:
            if field in data:
                data.pop(field)

        serializer = UserSignupSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class UserSignupView(APIView):
    def post(self, request):
        serializer = UserSignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'email': user.email,
                'height_cm': user.height_cm,
                'gender': user.gender,
                'weight_kg': user.weight_kg,
                'target_weight_kg': user.target_weight_kg,
                'age': user.age,
                'activity_level': user.activity_level,
                'join_date': user.join_date,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(email=email, password=password)
            if user is not None:
                token, created = Token.objects.get_or_create(user=user)
                return Response({'token': token.key}, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Ensure the user is authenticated
def logout_view(request):
    request.user.auth_token.delete()  # Delete the user's auth token
    return Response(status=status.HTTP_204_NO_CONTENT)

class DietLogItemViewSet(viewsets.ModelViewSet):
    serializer_class = DietLogItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return DietLogItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    @action(detail=False, methods=['post'], url_path='scan')
    def scan(self, request):
        image_file = request.FILES.get('image')
        if not image_file:
            return Response({"error": "No image provided."}, status=status.HTTP_400_BAD_REQUEST)
        gpt4o = GPTFoodScanner()

        try:
            result = gpt4o.analyze_food_image(image_file)
            return Response(result, status=status.HTTP_200_OK)
        except RuntimeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ExerciseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer


class WorkoutViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Workout.objects.all().prefetch_related(
        'workoutexercise_set__exercise'  # Prefetch related exercises efficiently
    )
    serializer_class = WorkoutSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Search functionality
        query = request.query_params.get('q', None)
        if query:
            queryset = queryset.filter(Q(name__icontains=query))
        
        # Filter by body_part
        body_part = request.query_params.get('body_part', None)
        # if body_part:
        #     queryset = queryset.filter(workoutexercise__exercise__body_part__icontains=body_part)
        if body_part:
            queryset = queryset.filter(body_part__icontains=body_part)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)  # Exercises are included automatically

    @action(detail=False, methods=['get'], url_path='featured-workouts')
    def featured_workouts(self, request, *args, **kwargs):
        """
        Custom action to fetch the featured workout for today.
        """
        today = date.today()
        try:
            # Filter FeaturedWorkout for today and get the first one
            featured = FeaturedWorkout.objects.filter(date=today)
            if not featured:
                return Response({"detail": "No featured workouts for today."}, status=404)

            # Serialize the associated workout
            serializer = self.get_serializer(featured.workout)
            return Response(serializer.data)
        except Exception as e:
            return Response({"detail": str(e)}, status=500)
    
    @action(detail=True, methods=['post'], url_path='subscribe')
    def subscribe(self, request, pk=None):
        """
        Subscribe to a workout by creating a program for 7 days.
        """
        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication is required to subscribe to a workout."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        user = request.user

        # Check if the user has an active subscription
        active_program = ActiveWorkoutProgram.objects.filter(user=user, is_active=True).first()
        if active_program:
            return Response(
                {"error": "You already have an active workout program."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch the workout by its ID (pk)
        try:
            workout = Workout.objects.get(pk=pk)
        except Workout.DoesNotExist:
            return Response({"error": "Workout not found."}, status=status.HTTP_404_NOT_FOUND)

        # Create a new Workout Program
        workout_program = WorkoutProgram.objects.create(
            user=user,
            name=f"Subscribed Program for Workout {workout.name}"
        )

        # Create ProgramDays for all 7 days
        for day in range(7):
            ProgramDay.objects.create(
                workout_program=workout_program,
                workout=workout,
                day_of_week=day
            )

        # Create an ActiveWorkoutProgram
        start_date = now()
        end_date = start_date + timedelta(days=30)
        active_workout_program = ActiveWorkoutProgram.objects.create(
            user=user,
            workout_program=workout_program,
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )

        # Return success response with workout and program IDs
        return Response(
            {
                "message": "Workout subscription created successfully.",
                "workout_program_id": workout_program.id,
                "workout_id": workout.id,
            },
            status=status.HTTP_201_CREATED
        )


    

class LoggedWorkoutViewSet(viewsets.ModelViewSet):
    serializer_class = LoggedWorkoutSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return LoggedWorkout.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        logged_workout = serializer.save(user=self.request.user)
        exercises_data = self.request.data.get('exercises', [])
        for exercise in exercises_data:
            # Retrieve the Exercise instance
            exercise_instance = get_object_or_404(Exercise, exercise_id=exercise["exercise_id"])
            
            LoggedExercise.objects.create(
                logged_workout=logged_workout,
                exercise=exercise_instance,  # Pass the instance instead of the ID
                order=exercise['order'],
                sets_completed=exercise["sets"],
                reps_completed=exercise["reps"],
                weight_used_kg=exercise.get('weight_in_kg', None),
                km_ran=exercise.get('km_ran', None),
            )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        data = self.get_serializer(instance).data
        exercises = LoggedExercise.objects.filter(logged_workout=instance).order_by('order')
        data['exercises'] = [
            {
                'exercise_id': ex.exercise.id,
                'name': ex.exercise.name,
                'sets_completed': ex.sets_completed,
                'reps_completed': ex.reps_completed,
                'weight_used_kg': ex.weight_used_kg,
                'km_ran': ex.km_ran
            }
            for ex in exercises
        ]
        return Response(data)

class WorkoutProgramViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A viewset for viewing Workout Programs and their associated Program Days.
    """
    queryset = WorkoutProgram.objects.all().prefetch_related('days')  # Prefetch ProgramDays to optimize queries
    serializer_class = WorkoutProgramSerializer
    permission_classes = [IsAuthenticated]  # Only authenticated users can access this view

    def get_queryset(self):
        """
        Optionally restricts the returned workouts to a given user,
        by filtering against a `user` query parameter in the URL.
        """
        queryset = super().get_queryset()
        user = self.request.user
        return queryset

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a workout program for the authenticated user.
        """
        program = self.get_object()

        # Check if the user has any active workout program
        active_program = ActiveWorkoutProgram.objects.filter(
            user=request.user, is_active=True
        ).first()
        if active_program:
            return Response(
                {'error': 'You already have an active workout program. Deactivate it first to activate another.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Activate the new program
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        ActiveWorkoutProgram.objects.create(
            workout_program=program,
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )
        return Response({'status': 'workout program activated'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Deactivate the active workout program for the authenticated user.
        """
        active_program = ActiveWorkoutProgram.objects.filter(
            workout_program_id=pk,
            user=request.user,
            is_active=True
        ).first()
        if active_program:
            active_program.is_active = False
            active_program.save()
            return Response({'status': 'workout program deactivated'})
        else:
            return Response({'error': 'No active workout program found'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def current_program(self, request):
        """
        Retrieve the latest active workout program for the authenticated user.
        """
        active_program = ActiveWorkoutProgram.objects.filter(user=request.user, is_active=True).order_by('-start_date').first()
        
        if active_program is None:
            return Response({'error': 'No active workout program found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = WorkoutProgramSerializer(active_program.workout_program)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def todays_workout(self, request):
        active_program = ActiveWorkoutProgram.objects.filter(
            user=request.user, is_active=True
        ).order_by('-start_date').first()

        if not active_program:
            return Response({'error': 'No active workout program found'}, status=status.HTTP_404_NOT_FOUND)

        day = get_current_day()  # Assuming this function returns an integer (0-6)
        todays_day = ProgramDay.objects.filter(
            workout_program=active_program.workout_program, day_of_week=day
        ).first()

        if todays_day and todays_day.workout:
            serializer = WorkoutSerializer(todays_day.workout)
            response_data = serializer.data
            response_data['workout_program_id'] = active_program.workout_program.id
            return Response(response_data)
        
        return Response({'message': 'Rest day', 'workout_program_id': active_program.workout_program.id})



class StatsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def calories_burned(self, request):
        """
        Total calories burned today by the authenticated user.
        """
        user = request.user
        today = datetime.now().date()

        # Sum up calories from logged exercises for today
        exercises_today = LoggedExercise.objects.filter(
            logged_workout__user=user,
            logged_workout__log_time__date=today
        ).select_related('exercise')

        total_calories_burned = sum(
            ex.sets_completed * ex.reps_completed * ex.exercise.calories_burned
            for ex in exercises_today
        )
        return Response({'calories_burned_today': total_calories_burned})

    @action(detail=False, methods=['get'])
    def calories_eaten(self, request):
        """
        Total calories eaten today by the authenticated user.
        """
        user = request.user
        today = datetime.now().date()

        # Sum up calories from diet log items for today
        calories_eaten = DietLogItem.objects.filter(
            user=user,
            log_time__date=today
        ).aggregate(total_calories=Sum('food_calories'))['total_calories'] or 0

        return Response({'calories_eaten_today': calories_eaten})

    @action(detail=False, methods=['get'])
    def calories_eaten_per_day(self, request):
        """
        Number of calories eaten for the past week on each weekday, starting Monday onward.
        """
        user = request.user
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())  # Get the last Monday

        # Initialize a dictionary to store calories for each day of the week
        calories_per_day = {start_of_week + timedelta(days=i): 0 for i in range(7)}

        # Get the calories eaten for the past week
        diet_logs = DietLogItem.objects.filter(
            user=user,
            log_time__date__gte=start_of_week,
            log_time__date__lte=today
        ).values('log_time__date').annotate(total_calories=Sum('food_calories'))

        # Update the dictionary with the actual calories eaten
        for log in diet_logs:
            log_date = log['log_time__date']
            calories_per_day[log_date] = log['total_calories']

        # Convert the dictionary to a list of calories starting from Monday
        calories_list = [calories_per_day[start_of_week + timedelta(days=i)] for i in range(7)]

        return Response({'calories_eaten_per_day': calories_list})

    @action(detail=False, methods=['get'])
    def calories_burned_per_day(self, request):
        """
        Number of calories burned for the past week on each weekday, starting Monday onward.
        """
        user = request.user
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())  # Get the last Monday

        # Initialize a dictionary to store calories for each day of the week
        calories_per_day = {start_of_week + timedelta(days=i): 0 for i in range(7)}

        # Get the exercises for the past week
        exercises = LoggedExercise.objects.filter(
            logged_workout__user=user,
            logged_workout__log_time__date__gte=start_of_week,
            logged_workout__log_time__date__lte=today
        ).select_related('exercise')

        # Calculate the total calories burned for each day
        for exercise in exercises:
            log_date = exercise.logged_workout.log_time.date()
            calories_burned = exercise.sets_completed * exercise.reps_completed * exercise.exercise.calories_burned
            calories_per_day[log_date] += calories_burned

        # Convert the dictionary to a list of calories starting from Monday
        calories_list = [calories_per_day[start_of_week + timedelta(days=i)] for i in range(7)]

        return Response({'calories_burned_per_day': calories_list})

    @action(detail=False, methods=['get'])
    def number_exercises(self, request):
        """
        Total number of exercises done by the authenticated user.
        """
        user = request.user.userprofile
        exercise_count = LoggedExercise.objects.filter(
            logged_workout__user=user
        ).count()
        return Response({'number_of_exercises': exercise_count})

    @action(detail=False, methods=['get'])
    def number_logged_exercises_per_day(self, request):
        """
        Number of logged exercises per day for the last 30 days.
        """
        user = request.user.userprofile
        last_30_days = datetime.now() - timedelta(days=30)

        exercise_logs = LoggedExercise.objects.filter(
            logged_workout__user=user,
            logged_workout__log_time__gte=last_30_days
        ).values('logged_workout__log_time__date').annotate(count=Count('id'))

        data = {log['logged_workout__log_time__date']: log['count'] for log in exercise_logs}
        return Response({'number_logged_exercises_per_day': data})