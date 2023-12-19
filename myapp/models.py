
from .models import *

from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin


class Item(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


    
class Charger(models.Model):
    plug_type = models.CharField('Plug Type' ,max_length=200)
    speed = models.CharField('Charging Speed', max_length=200)

    def __str__(self):
        return self.plug_type + " " + self.speed + "KVh"

class Car(models.Model):
    brand = models.CharField('Brand' ,max_length=200)
    car_model = models.CharField('Model', max_length=200)
    battery_pack_kwh = models.CharField('battery_pack_kwh', max_length=200)
    plug_type = models.CharField('Plug Type',default="", max_length=100)
    def __str__(self):
        return (f"{self.brand} - {self.car_model} - {self.plug_type}")
    

class UserCars(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cars = models.ManyToManyField(Car)

    def __str__(self):
        return f"{self.user.username}"


class ChargingStation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.CharField('address', max_length=200)
    charger = models.ForeignKey(Charger, null=True, on_delete=models.CASCADE)
    description = models.CharField('description', null=True, max_length=200)
    working_hours_start = models.TimeField('working hours start', null=True)
    working_hours_finish = models.TimeField('working hours finish', null=True)
    station_status = models.CharField('station status', max_length=100, choices=[('Used', 'Used'), ('Available', 'Available'), ('Off', 'Off')], default='Available')

    def __str__(self):
        return f'{self.user} {self.address} {self.charger}'
    

class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)    
    charging_stations = models.ManyToManyField(ChargingStation, blank=True)
    cars = models.ManyToManyField(Car, blank=True)
    max_walking_distance = models.PositiveIntegerField(default=1000)

    def __str__(self):
        return f"Profile for {self.user.first_name} {self.user.last_name}"    
    
    
class User(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    password = models.CharField(max_length=128)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    
    
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'max_walking_distance']


class Media(models.Model):
    image_name = models.CharField(max_length=100, default="image", null=False)
    image = models.ImageField(null=True, blank=True, upload_to="images/")

    def __str__(self):
        return self.image_name


    