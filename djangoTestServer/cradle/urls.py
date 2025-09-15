from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register_cradle/', views.register_cradle, name='register_cradle'),
    path('register_agent/', views.register_agent, name='register_agent'),
    path('stream/<str:uuid>/', views.video_feed, name='video_feed'),
    path('control_motor/<str:uuid>/', views.control_motor, name='control_motor'),
    path('crying_status/<str:uuid>/', views.crying_status, name='crying_status'),
    path('direction_status/<str:uuid>/', views.direction_status, name='direction_status'),
    path('get_sensor_data/<str:uuid>/', views.get_sensor_data, name='get_sensor_data'),
]