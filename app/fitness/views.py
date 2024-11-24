# core/views.py
from rest_framework import permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from datetime import datetime, timedelta
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
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)  # Exercises are included automatically

    @action(detail=False, methods=['get'])
    def search(self, request, *args, **kwargs):
        """
        Custom search endpoint (optional if list handles it directly)
        """
        query = request.query_params.get('q', None)
        queryset = self.get_queryset()
        if query:
            queryset = queryset.filter(Q(name__icontains=query))
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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
        program = self.get_object()
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

# @action(detail=False, methods=['get'])
# def todays_workout(self, request):
#     active_program = ActiveWorkoutProgram.objects.filter(user=request.user, is_active=True).order_by('-start_date').first()
    
#     if active_program is None:
#         return Response({'error': 'No active workout program found'}, status=status.HTTP_404_NOT_FOUND)
    
#     program_days = ProgramDay.objects.filter(workout_program=active_program.workout_program)
#     day = get_current_day()  # Assuming this function returns an integer (0-6)
#     todays_day = program_days.filter(day_of_week=day).first()  # Call the function here

#     if todays_day and todays_day.workout:
#         exercises = WorkoutExercise.objects.filter(workout=todays_day.workout).order_by('order')
#         response_data = {
#             'workout_name': todays_day.workout.name,
#             'description': todays_day.workout.description,
#             'exercises': [
#                 {
#                     'exercise_id': ex.exercise.id,
#                     'name': ex.exercise.name,
#                     'sets': ex.sets,
#                     'reps': ex.reps,
#                     'weight_in_kg': ex.weight_in_kg,
#                     'km_ran': ex.km_ran
#                 }
#                 for ex in exercises
#             ]
#         }
#         return Response(response_data)
    
#     return Response({'message': 'Rest day'})

class ActiveWorkoutProgramViewSet(viewsets.ModelViewSet):
    queryset = ActiveWorkoutProgram.objects.all()
    serializer_class = WorkoutProgramSerializer

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        program = self.get_object()
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
    def todays_workout(self, request):
        active_program = ActiveWorkoutProgram.objects.filter(user=request.user, is_active=True).order_by('-start_date').first()
        if active_program:
            today = datetime.now().weekday()
            todays_day = ProgramDay.objects.filter(workout_program=active_program.workout_program, day_of_week=today).first()
            if todays_day and todays_day.workout:
                workout_serializer = WorkoutSerializer(todays_day.workout)
                return Response(workout_serializer.data)
            return Response({'message': 'Rest day'})
        return Response({'message': 'No active workout program found'}, status=status.HTTP_404_NOT_FOUND)