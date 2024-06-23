from django.contrib import admin
from django.contrib.auth.models import Group,User
from myapp.models import Profile 
from .models import *

# Register your models here.
#admin.site.register(Messege)
admin.site.register(Car)
admin.site.register(Charger)
admin.site.register(ChargingStation)
admin.site.register(Profile)
admin.site.register(Media)
admin.site.register(UserCars)
admin.site.register(ChargingStationSchedule)
admin.site.register(ChargingStationOrder)