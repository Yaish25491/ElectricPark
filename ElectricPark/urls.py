"""
URL configuration for ElectricPark project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from myapp import views
from django.conf import settings
from django.conf.urls.static import static
from myapp.views import *
from myapp.models import *

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.index, name="index"),
    path("landing_page/", views.landing_page, name="Landing Page"),
    path("login/choose_a_car/", views.choose_a_car, name="Choose A Car"),
    path("login/create_charging_sation/", views.create_charging_station, name="Create A Charging Station"),
    path("login/home/", views.home, name="home"),
    path("register/", views.register_user, name="register"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("login/active_orders/", views.active_orders, name="active orders"),
    path("login/order_history/", views.order_history, name="order history"),
    path('export_order_history_to_csv/', export_order_history_to_csv, name='export_order_history_to_csv'),
    path("login/user_settings/", views.user_settings, name="user settings"),
    path("login/your_charging_stations/", views.charging_stations, name="your charging stations"),
    path("login/test_page/", views.test_page, name="test page"),
    path("login/uploade_csv/", views.upload_csv, name="upload_csv"),
    path("login/export_records/", views.export_records, name="export_records"),
    path("login/db_control/", views.DBcontrol, name="DBcontrol"),
    path('get_addresses/', get_addresses, name='get_addresses'),
    path('login/update_charging_station/', views.update_charging_station, name='update_charging_station'),
    path('edit_working_hours/', views.edit_working_hours, name='edit_working_hours'),
    path('profile/', Profile, name='profile'),
    path('login/search/', views.search_charging_stations, name='search_charging_stations'),
    path('', views.home, name='home'),
    path('update_max_walking_distance/', views.update_max_walking_distance, name='update_max_walking_distance'),
    path('delete_user_car/<int:car_id>/', delete_user_car, name='delete_user_car'),
    path('get_info/', views.get_info, name='get_info'),
    path('schedule/<int:station_id>/', schedule_station, name='schedule_station'),
    path('process_schedule/<int:station_id>/', process_schedule, name='process_schedule'),
    path('login/manage_schedule/<int:station_id>/', manage_schedule, name='manage_schedule'),
    path('login/calendar/<int:station_id>/', views.weekly_calendar, name='weekly_calendar'),
    #path('available-times/<int:station_id>/<str:order_date>/', views.get_available_times, name='get_available_times'),
    path('schedule/<int:station_id>/', schedule_station, name='schedule_station'),
    path('get-available-times/<int:station_id>/', views.get_available_times, name='get_available_times'),
    path('charging-stations/', views.charging_stations, name='charging_stations'),
    path('open_orders/<int:charging_station_id>/', views.open_orders_by_id, name='open_orders_by_id'),
    path('order_history/<int:charging_station_id>/', views.order_history_by_id, name='order_history_by_id'),
    path('export_order_history_to_csv/<int:charging_station_id>/', views.export_order_history_to_csv, name='export_order_history_to_csv'),


]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
