# core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'dietlogitems', DietLogItemViewSet, basename='dietlogitem')
router.register(r'exercises', ExerciseViewSet, basename='exercise')
router.register(r'workouts', WorkoutViewSet, basename='workout')
router.register(r'workoutprograms', WorkoutProgramViewSet, basename='workoutprogram')
router.register(r'loggedworkouts', LoggedWorkoutViewSet, basename='loggedworkout')
router.register(r'activeworkoutprograms', ActiveWorkoutProgramViewSet, basename='activeworkoutprogram')
router.register(r'stats', StatsViewSet, basename='stats')


urlpatterns = [
    path('', include(router.urls)),
    path('activeworkoutprograms/<int:pk>/activate/', ActiveWorkoutProgramViewSet.as_view({'post': 'activate'})),
    path('activeworkoutprograms/<int:pk>/deactivate/', ActiveWorkoutProgramViewSet.as_view({'post': 'deactivate'})),
    path('activeworkoutprograms/todays_workout/', ActiveWorkoutProgramViewSet.as_view({'get': 'todays_workout'})),
    path('signup/', UserSignupView.as_view(), name='signup'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('logout/', logout_view, name='logout'),
]
