import datetime, csv, os, googlemaps, logging
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

from .forms import *
from .models import *

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.management.base import BaseCommand
from django.http import HttpResponse, JsonResponse
from django.db import connection, connections
from django.core.exceptions import ValidationError
from operator import itemgetter
from django.utils import timezone
from datetime import datetime, timedelta, time



def index(request):
    if request.user.is_authenticated:
        return redirect('login/home')
    else:   
        
        return render(request, "index.html")

def landing_page(request):
    return render(request, "LandingPage.html", {})



def choose_a_car(request):
    form = CarSelectionForm()

    if request.method == 'POST':
        form = CarSelectionForm(request.POST)
        if form.is_valid():
            selected_car_id = form.cleaned_data['car']
            user_cars, created = UserCars.objects.get_or_create(user=request.user)

            # Associate the selected car with the user's profile using SQL
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO myapp_usercars_cars (usercars_id, car_id)
                    VALUES (%s, %s)
                    """,
                    [user_cars.id, selected_car_id.id]
                )

            messages.success(request, 'Car added successfully!')
            return redirect('Choose A Car')

    context = {
        'form': form,
    }
    return render(request, 'ChooseACar.html', context)

def delete_user_car(request, car_id):
    if request.method == 'POST':
        form = DeleteCarForm(request.POST)
        if form.is_valid():
            car_id = form.cleaned_data['car_id']
            return redirect('user_settings')
    else:
        form = DeleteCarForm(initial={'car_id': car_id})

    context = {'form': form}
    return render(request, 'UserSettings.html', context)

def create_charging_station(request):
    if request.method == 'POST':
        form = ChargingStationForm(request.POST)
        if form.is_valid():
            charging_station = form.save(commit=False)
            charging_station.user = request.user
            charging_station.save()
            messages.success(request, 'Charging station created successfully!')
            form = ChargingStationForm()
    else:
        form = ChargingStationForm()

    context = {'form': form}
    return render(request, 'CreateAChargingStation.html', context)
    

def home(request):
    print("Home")
    charging_stations = ChargingStation.objects.all()
    charging_station_distances = []

    if request.method == 'POST':
        form = ChargingStationSearchForm(request.user, request.POST)
        if form.is_valid():
            user_address = form.cleaned_data['address']  # Use the user's input address

            selected_car_name = form.cleaned_data['car'].id

            # Step 1: Get the car's plug_type
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT plug_type
                    FROM myapp_car
                    WHERE id = %s
                    """,
                    [selected_car_name]
                )
                plug_type = cursor.fetchone()

            if plug_type:
                plug_type = plug_type[0]

                # Step 2: Get the plug_type_id from myapp_charger
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id
                        FROM myapp_charger
                        WHERE plug_type = %s
                        """,
                        [plug_type]
                    )
                    plug_type_id = cursor.fetchone()

                if plug_type_id:
                    plug_type_id = plug_type_id[0]

                    # Step 3: Get the compatible charging stations from myapp_chargingstation
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            SELECT id, address
                            FROM myapp_chargingstation
                            WHERE charger_id = %s
                            """,
                            [plug_type_id]
                        )
                        charging_stations = cursor.fetchall()

                        # Step 4: Requires API key for Google Maps API
                        gmaps = googlemaps.Client(key='AIzaSyCBlESR_sT43qVHo5P3Jquk9SuHsZwpL6Q')

                        # Step 5: Iterate through each charging station
                        for charging_station in charging_stations:
                            charging_station_id, charging_station_address = charging_station

                            # Step 6: Use Google Maps Distance Matrix API to calculate distance
                            distance_matrix = gmaps.distance_matrix(user_address, charging_station_address)['rows'][0]['elements'][0]
                            distance = distance_matrix['distance']['value'] if 'distance' in distance_matrix else 'N/A'
                            distance_text = distance_matrix['distance']['text'] if 'distance' in distance_matrix else 'N/A'

                            # Custom validation for invalid address
                            if distance == 'N/A':
                                messages.error(request,"Invalid Address, please use a street, building number and a city combination")
                                context = {'form': form}
                                return render(request, 'home.html', context)

                            # Step 7: Append charging station address and distance to the list
                            charging_station_distances.append({
                                'id': charging_station_id,
                                'address': charging_station_address,
                                'distance': distance,
                                'distance_text': distance_text
                            })

    else:
        form = ChargingStationSearchForm(user=request.user)

    # Step 8: Filter charging stations based on max_walking_distance
    max_walking_distance = None
    filtered_charging_stations = []

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT max_walking_distance
            FROM myapp_profile
            WHERE user_id = %s
            """,
            [request.user.id]
        )
        result = cursor.fetchone()
        max_walking_distance = float(result[0]) if result is not None else None

    if max_walking_distance is not None:
        # Ensure that the distance field is a string with both value and unit
        charging_station_distances_numeric = [
            {
                'id': station['id'],
                'address': station['address'],
                'distance': f"{station['distance']} m",  # Assuming distance is in meters
                'distance_text': station['distance_text'],
            }
            for station in charging_station_distances
        ]
        print("********** results before filtering strats here **********")
        print(charging_station_distances_numeric)
        print("********** results ends here **********")
        # Step 9: Filter charging stations based on max_walking_distance
        charging_station_distances_numeric = [
            {
                'id': station['id'],
                'address': station['address'],
                'distance': f"{station['distance']} m",  # Assuming distance is in meters
                'distance_text': station['distance_text'],
            }
            for station in charging_station_distances
        ]

        # Step 9.1: Sort charging stations by distance
        charging_station_distances_numeric.sort(key=lambda x: float(x['distance'].split(' ')[0]))

        # Step 9.2: Filter charging stations based on max_walking_distance
        filtered_charging_stations = [
            {
                'id': station['id'],
                'address': station['address'],
                'distance': station['distance'],
                'distance_text': station['distance_text'],
                'max': max_walking_distance,
            }
            for station in charging_station_distances_numeric
            if float(station['distance'].split(' ')[0]) <= max_walking_distance
        ]
    

        # Step 10: Print the difference for each filtered charging station
        for station in filtered_charging_stations:
            distance_numeric = float(station['distance'].split(' ')[0])
            difference = distance_numeric - max_walking_distance
            print(f"Distance: {distance_numeric} m, Max Walking Distance: {max_walking_distance} m, Difference: {difference} m")

        # Step 11: Check if results are empty and show error message
        if not filtered_charging_stations:
            messages.error(request, "There are no Charging Stations in the erea you searched, Please update your max walking distance to get results")
        else:
                # Step 12: Add messages based on the number of results
                num_results = len(filtered_charging_stations)
                if 1 <= num_results <= 5:
                    messages.success(request, f"Your search returned with {num_results} result{'s' if num_results > 1 else ''}.")
                elif num_results > 5:
                    messages.success(request, f"Your search returned with {num_results} results. Here are the top 5.")

        
        #step 13: filter list to be top 5 results
        filtered_charging_stations = filtered_charging_stations[:5]
    
    else:
        form = ChargingStationSearchForm(user=request.user)

    context = {
        'form': form,
        'charging_stations': filtered_charging_stations,
        'charging_station_distances': charging_station_distances,
    }
    print("********** results strats here **********")
    print(filtered_charging_stations)
    print("********** results ends here **********")
    return render(request, 'Home.html', context)


def schedule_station(request, station_id):
    charging_station = ChargingStation.objects.get(id=station_id)
    # Add logic to get available time windows for scheduling
    return render(request, 'schedule_station.html', {'charging_station': charging_station, 'available_time_windows': available_time_windows})

def process_schedule(request, station_id):
    if request.method == 'POST':
        # Add logic to handle the form submission and schedule the time window
        # Make sure to check if the selected time window is available
        # Update the ChargingStationSchedule table accordingly
        return redirect('home')


def new_user(request):
    return render(request, "NewUser.html", {})


def dropdown_view(request):
    items = Item.objects.all()
    return render(request, 'ChooseACar.html', {'Maker': items})

def register_user(request):
    form = SignUpForm()
    
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            new_user = form.save()

            # Log in user
            user = authenticate(username=new_user.username, password=form.cleaned_data['password1'])
            login(request, user)

            # Automatically create a profile for the user
            Profile.objects.create(user=new_user, max_walking_distance=1000)

            # Automatically create a UserCars for the user
            UserCars.objects.create(user=new_user)

            messages.success(request, f"You have successfully registered! Welcome! Your user ID is {new_user.id}.")
            return redirect('Choose A Car')

    return render(request, "register.html", {'form': form})

def login_user(request):
	if request.method == "POST":
		username = request.POST['username']
		password = request.POST['password']
		user = authenticate(request, username=username, password=password)
		if user is not None:
			login(request, user)
			return redirect('home')
		else:
			messages.success(request, ("There Was An Error Logging In, Try Again..."))	
			return redirect('login')	


	else:
		return render(request, 'login.html', {})

def logout_user(request):
	logout(request)
	messages.success(request, ("You Were Logged Out!"))
	return redirect('index')

def active_orders(request):
    return render(request, "ActiveOrders.html", {})


from django.contrib.auth.decorators import login_required
from django.db import connection
from django.shortcuts import render

@login_required
def order_history(request):
    user_id = request.user.id
    
    # Fetch order history for the logged-in user using raw SQL
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT o.id, o.order_date, o.order_start, o.order_finish, s.address
            FROM myapp_chargingstationorder o
            JOIN myapp_chargingstation s ON o.charging_station_id = s.id
            WHERE o.user_id = %s
            ORDER BY o.order_date DESC, o.order_start DESC
            """,
            [user_id]
        )
        orders = cursor.fetchall()
    
    return render(request, "OrderHistory.html", {'orders': orders})





@login_required
def user_settings(request):
    # Retrieve user details from the auth_user table
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT first_name, last_name, username, email
            FROM auth_user
            WHERE id = %s
            """,
            [request.user.id]
        )
        user_details = dict(zip([col[0] for col in cursor.description], cursor.fetchone()))

    # Retrieve max_walking_distance from the myapp_profile table
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT max_walking_distance
            FROM myapp_profile
            WHERE user_id = %s
            """,
            [request.user.id]
        )
        result = cursor.fetchone()
        max_walking_distance = result[0] if result is not None else None

    # Retrieve USERCARS_ID using users id
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id
            FROM myapp_usercars
            WHERE user_id = %s
            """,
            [request.user.id]
        )
        usercars_id_result = cursor.fetchone()
        
    # Check if usercars_id_result is not None before using it
    if usercars_id_result is not None:
        usercars_id = usercars_id_result[0]

        # Retrieve user's cars from the myapp_usercars table
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT brand, car_model, plug_type
                FROM myapp_usercars_cars
                INNER JOIN myapp_car ON myapp_usercars_cars.car_id = myapp_car.id
                WHERE usercars_id = %s
                """,
                [usercars_id]
            )
            user_cars = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    else:
        user_cars = []

    context = {
        'user_details': user_details,
        'max_walking_distance': max_walking_distance,
        'user_cars': user_cars,
    }

    return render(request, 'UserSettings.html', context)




def your_charging_stations(request):
    return render(request, "YourChargingStations.html", {})

def test_page(request):
    return render(request, "testpage.html", {})

def DBcontrol(request):
    return render(request, "DBcontrol.html", {})




@login_required
def charging_stations(request):
    user = request.user
    charging_stations = ChargingStation.objects.filter(user=user)

    if request.method == 'POST':
        form = ChargingStationForm(request.POST)
        if form.is_valid():
            charging_station = ChargingStation.objects.get(id=form.cleaned_data['charging_station_id'])
            charging_station.working_hours_start = form.cleaned_data['working_hours_start']
            charging_station.working_hours_finish = form.cleaned_data['working_hours_finish']
            charging_station.save()

    form = ChargingStationViewForm()

    context = {
        'charging_stations': charging_stations,
        'form': form,
    }

    return render(request, 'charging_stations.html', context)



def update_charging_station(request):
    user = request.user
    
    if request.method == 'POST':
        
        form = ChargingStationUpdateForm(user, request.POST)
        if form.is_valid():
            charging_station = form.cleaned_data['charging_station']
            charging_station.working_hours_start = form.cleaned_data['working_hours_start']
            charging_station.working_hours_finish = form.cleaned_data['working_hours_finish']
            charging_station.save()
            return redirect('home')  # Redirect to your desired page
    else:
        form = ChargingStationUpdateForm(user)

    context = {'form': form}
    return render(request, 'update_charging_station.html', context)


class Command(BaseCommand):
    help = 'Updates Car database table from a CSV file'

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']

        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                brand = row['Brand']
                model = row['Model']
                plug_type = row['PlugType']
                battery_pack_kwh = row['Battery_Pack_Kwh']
                
                car, created = Car.objects.update_or_create(
                    brand=brand, car_model=model,
                    defaults={'plug_type': plug_type, 'battery_pack_kwh': battery_pack_kwh}
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created new Car: {car}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'Updated Car: {car}'))

def custom_charging_stations_view(request):

    user = request.user  # Get the currently logged-in user

    # Construct the SQL query
    sql_query = """
    SELECT id, address, charger_id, description, status, working_hours_start, working_hours_finish
    FROM your_app_chargingstation
    WHERE user_id = %s
    """

    # Execute the SQL query
    with connection.cursor() as cursor:
        cursor.execute(sql_query, [user.id])

        # Fetch the results
        charging_stations = cursor.fetchall()

    # You can print the SQL query here for debugging
    print(sql_query)

    return render(
        request,
        "myapp/charging_stations.html",
        {"charging_stations": charging_stations},
    )

def edit_working_hours(request, charging_station_id):
    if request.method == 'POST':
        charging_station = ChargingStation.objects.get(pk=charging_station_id)
        form = ChargingStationForm(request.POST, instance=charging_station)
        if form.is_valid():
            form.save()
            return redirect('charging_stations')
    
    # Handle invalid form or GET request here
    return redirect('charging_stations')

def upload_csv(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data['csv_file']
            # Save the uploaded file temporarily
            with open('temp.csv', 'wb') as temp_file:
                for chunk in csv_file.chunks():
                    temp_file.write(chunk)
            # Run the management command to update the database
            command = Command()
            command.handle(csv_file='temp.csv')
            # Delete the temporary file
            os.remove('temp.csv')
            messages.success(request, 'CSV file uploaded and database updated.')
            return redirect('upload_csv')
    else:
        form = CSVUploadForm()
    
    context = {'form': form}
    return render(request, 'upload_csv.html', context)


def export_csv(request):
    if request.method == 'POST':
        form = DBSelectionForm(request.POST)
        if form.is_valid():
            selected_table = form.cleaned_data['table']
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{selected_table}.csv"'

            cursor = connections['default'].cursor()
            cursor.execute(f'SELECT * FROM {selected_table}')
            
            csv_writer = csv.writer(response)
            csv_writer.writerow([desc[0] for desc in cursor.description])  # Write column headers
            csv_writer.writerows(cursor)

            return response
    else:
        form = DBSelectionForm()
    
    context = {
        'form': form,
    }
    return render(request, 'export_csv.html', context)


def export_records(request):
    if request.method == 'POST':
        form = ExportForm(request.POST)
        if form.is_valid():
            selected_table = form.cleaned_data['table']
            # Fetch records from the selected table
            cursor = connections['default'].cursor()
            cursor.execute(f'SELECT * FROM {selected_table}')
            records = cursor.fetchall()

            # Create a CSV content
            csv_content = '\n'.join([','.join(map(str, row)) for row in records])
            
            # Create the HTTP response with CSV content
            response = HttpResponse(csv_content, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{selected_table}_export.csv"'
            return response
    else:
        form = ExportForm()

    context = {
        'form': form,
    }
    return render(request, 'export_records.html', context)



def get_addresses(request):
    addresses = ChargingStation.objects.values_list('address', flat=True)
    return JsonResponse(list(addresses), safe=False)


def get_info(request):
    address = request.GET.get('address')
    
    charging_stations = ChargingStation.objects.filter(address=address)
    
    if charging_stations.exists():
        # If there are multiple charging stations, include information for all of them
        data = [{
            'charger': str(charging_station.charger),  # Convert Charger object to string
            'description': charging_station.description,
        } for charging_station in charging_stations]
        print(data)
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({'error': 'Charging station not found'}, status=404)





def display_logo(request):
    # Retrieve the image data by its name, assuming the name is 'ElectricPark logo'
    image_data = Media.objects.get(image_name='my_image.png')
    
    return render(request, 'image_display.html', {'image_data': image_data})

def display_image(request):
    return render(request, 'testpage.html')




def search_charging_stations(request):
    # Ensure the user is logged in

    user = request.user  # Get the currently logged-in user

    # Construct the SQL query
    sql_query = "SELECT id, car_model FROM myapp_car WHERE user_id = %s"

    # Execute the SQL query
    with connection.cursor() as cursor:
        cursor.execute(sql_query, [user.id])

        # Fetch the results
        charging_stations = cursor.fetchall()

    # You can print the SQL query here for debugging
    print(sql_query)

    return render(
        request,
        "myapp/charging_stations.html",
        {"charging_stations": charging_stations},
    )


@login_required
def update_max_walking_distance(request):
    if request.method == 'POST':
        max_walking_distance = request.POST.get('max_walking_distance')
        
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE myapp_profile
                SET max_walking_distance = %s
                WHERE user_id = %s
                """,
                [max_walking_distance, request.user.id]
            )

        messages.error(request, "Walking distance updated successfuly!")
    else:
        messages.error(request, "Walking distance updated unsuccessfuly!")

    return redirect("user settings")



def distance_calculation(request):
    # Step 1: Get the user's address from the request's GET parameters
    user_address = request.GET.get('address')
    
    # Step 2: Initialize an empty list to store charging station addresses and distances
    charging_station_distances = []

    # Step 3: Fetch all charging station IDs and addresses from the database
    with connection.cursor() as cursor:
        cursor.execute('SELECT id, address FROM myapp_chargingstation')
        charging_stations = cursor.fetchall()

    # Step 4: Requires API key for Google Maps API
    gmaps = googlemaps.Client(key='AIzaSyCBlESR_sT43qVHo5P3Jquk9SuHsZwpL6Q&callback=initMap')

    # Step 5: Iterate through each charging station
    for charging_station in charging_stations:
        charging_station_id, charging_station_address = charging_station

        # Step 6: Use Google Maps Distance Matrix API to calculate distance
        distance_matrix = gmaps.distance_matrix(user_address, charging_station_address)['rows'][0]['elements'][0]
        distance = distance_matrix['distance']['text'] if 'distance' in distance_matrix else 'N/A'

        # Step 7: Append charging station address and distance to the list
        charging_station_distances.append({
            'id': charging_station_id,
            'address': charging_station_address,
            'distance': distance
        })

    # Step 8: Return the list of charging station addresses and distances
    return charging_station_distances

def schedule_station(request, station_id):
    charging_station = ChargingStation.objects.get(id=station_id)
    available_time_windows = get_available_time_windows(charging_station)

    if request.method == 'POST':
        form = ChargingStationScheduleForm(request.POST)
        if form.is_valid():
            scheduled_time_start = form.cleaned_data['scheduled_time_start']
            scheduled_time_finish = form.cleaned_data['scheduled_time_finish']

            if is_time_window_available(charging_station, scheduled_time_start, scheduled_time_finish):
                ChargingStationSchedule.objects.create(
                    charging_station=charging_station,
                    user=request.user,
                    scheduled_time_start=scheduled_time_start,
                    scheduled_time_finish=scheduled_time_finish
                )
                messages.success(request, 'Charging station scheduled successfully.')
                return redirect('home')
            else:
                messages.error(request, 'Selected time window is not available.')
    else:
        form = ChargingStationScheduleForm()

    return render(request, 'schedule_station.html', {'charging_station': charging_station, 'available_time_windows': available_time_windows, 'form': form})


def is_time_window_available(charging_station, start_time, finish_time):
    # Your existing logic to check if the time window is available
    # ...

    # Assuming you have a method to get existing schedules for the charging station
    existing_schedules = ChargingStationSchedule.objects.filter(
        charging_station=charging_station,
        scheduled_time_finish__gt=timezone.now()  # Filter out past schedules
    )

    # Check if the new time window overlaps with existing schedules
    for schedule in existing_schedules:
        if start_time < schedule.scheduled_time_finish and finish_time > schedule.scheduled_time_start:
            return False  # Overlapping time window found

    return True

def process_schedule(request, station_id):
    if request.method == 'POST':
        form = ChargingStationScheduleForm(request.POST)
        if form.is_valid():
            start_time = form.cleaned_data['scheduled_time_start']
            finish_time = form.cleaned_data['scheduled_time_finish']

            charging_station = ChargingStation.objects.get(id=station_id)

            # Check if the selected time window is available
            if is_time_window_available(charging_station, start_time, finish_time):
                # Schedule the time window
                ChargingStationSchedule.objects.create(
                    charging_station=charging_station,
                    user=request.user,
                    scheduled_time_start=start_time,
                    scheduled_time_finish=finish_time
                )
                messages.success(request, 'Charging station scheduled successfully!')
                return redirect('home')
            else:
                messages.error(request, 'Selected time window is not available. Please choose another time.')
    else:
        form = ChargingStationScheduleForm()

    charging_station = ChargingStation.objects.get(id=station_id)
    available_time_windows = get_available_time_windows(charging_station)

    context = {
        'form': form,
        'charging_station': charging_station,
        'available_time_windows': available_time_windows,
    }

    return render(request, 'schedule_station.html', context)

def get_available_time_windows(charging_station):
    working_hours_start = charging_station.working_hours_start
    working_hours_finish = charging_station.working_hours_finish

    existing_schedules = ChargingStationSchedule.objects.filter(
        charging_station=charging_station,
        scheduled_time_finish__gt=timezone.now()
    )

    # Your logic to determine available time windows based on working hours and existing schedules
    # For simplicity, let's assume available time windows are every 30 minutes within working hours

    available_time_windows = []
    current_time = working_hours_start

    while current_time < working_hours_finish:
        end_time = current_time + timezone.timedelta(minutes=30)

        # Check if the time window overlaps with existing schedules
        overlap = any(
            schedule.scheduled_time_start < end_time and schedule.scheduled_time_finish > current_time
            for schedule in existing_schedules
        )

        if not overlap:
            available_time_windows.append((current_time, end_time))

        current_time = end_time

    return available_time_windows

def manage_schedule(request, station_id):
    charging_station = ChargingStation.objects.get(id=station_id)
    schedule_form = ChargingStationScheduleForm()

    if request.method == 'POST':
        schedule_form = ChargingStationScheduleForm(request.POST)
        if schedule_form.is_valid():
            scheduled_time_start = schedule_form.cleaned_data['scheduled_time_start']
            scheduled_time_finish = schedule_form.cleaned_data['scheduled_time_finish']

            # Check if the selected time window is available
            if is_time_window_available(charging_station, scheduled_time_start, scheduled_time_finish):
                # Create a new schedule entry
                ChargingStationSchedule.objects.create(
                    charging_station=charging_station,
                    user=request.user,
                    scheduled_time_start=scheduled_time_start,
                    scheduled_time_finish=scheduled_time_finish
                )

                # You can customize the success message
                messages.success(request, 'Charging station scheduled successfully.')

                # Redirect to the home page or any other appropriate page
                return redirect('home')
            else:
                messages.error(request, 'Selected time window is not available.')

    # Retrieve existing schedules for the charging station
    existing_schedules = ChargingStationSchedule.objects.filter(charging_station=charging_station)

    # Pass the charging station, existing schedules, and the form to the template
    context = {
        'charging_station': charging_station,
        'existing_schedules': existing_schedules,
        'schedule_form': schedule_form,
    }

    return render(request, 'manage_schedule.html', context)

from django.shortcuts import render, get_object_or_404
from .models import ChargingStation
from datetime import datetime, timedelta

def weekly_calendar(request, station_id):
    charging_station = get_object_or_404(ChargingStation, id=station_id)
    
    # Prepare the weekly calendar with 30-minute slots
    calendar = []
    start_time = charging_station.working_hours_start
    end_time = charging_station.working_hours_finish
    
    for day in range(7):
        slots = []
        current_time = datetime.combine(datetime.today(), start_time)
        end_time_today = datetime.combine(datetime.today(), end_time)
        while current_time < end_time_today:
            slots.append(current_time.time())
            current_time += timedelta(minutes=30)
        calendar.append(slots)
    
    context = {
        'charging_station': charging_station,
        'calendar': calendar,
    }
    
    return render(request, 'weekly_calendar.html', context)

from django.shortcuts import render
from datetime import time, timedelta, datetime
from .models import ChargingStation

def generate_time_slots(start, end, slot_duration):
    slots = []
    current = start
    while current <= end:
        slots.append(current)
        current = (datetime.combine(datetime.today(), current) + slot_duration).time()
    return slots

def show_weekly_calendar(request, station_id):
    charging_station = ChargingStation.objects.get(id=station_id)
    
    # Generate 30-minute time slots for a full 24 hours
    start_time = time(0, 0)
    end_time = time(23, 30)  # Ensure the last slot is included
    slot_duration = timedelta(minutes=30)
    time_slots = generate_time_slots(start_time, end_time, slot_duration)
    
    # Get working hours from the charging station object
    working_hours_start = charging_station.working_hours_start
    working_hours_finish = charging_station.working_hours_finish

    calendar = []
    for day in ['sunday', 'monday', 'tuesday', ' wednesday', 'thursday', 'friday', 'saturday']:
        day_slots = []
        for slot in time_slots:
            # Check if the slot falls within working hours for the current day
            if working_hours_start <= slot <= working_hours_finish:
                day_slots.append(slot)
        calendar.append(day_slots)
    
    context = {
        'charging_station': charging_station,
        'calendar': calendar,
        'time_slots': time_slots,
    }
    
    return render(request, 'weekly_calendar.html', context)


# views.py
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from .forms import ChargingStationOrderForm

@login_required
def schedule_station(request, station_id):
    # Fetch the station details using raw SQL
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, address
            FROM myapp_chargingstation
            WHERE id = %s
            """,
            [station_id]
        )
        station = cursor.fetchone()

    if not station:
        # Return a 404 error if the station is not found
        return HttpResponse(status=404)

    station_id, station_address = station

    if request.method == 'POST':
        form = ChargingStationOrderForm(request.POST)
        print("*** POST Data dict ***")
        print(request.POST.dict())
        if form.is_valid():
            order_date = form.cleaned_data['order_date']
            print(order_date)
            order_start = form.cleaned_data['order_start'].strftime('%H:%M:%S')
            print(order_start)
            order_finish = form.cleaned_data['order_finish'].strftime('%H:%M:%S')
            print(order_finish)
            user_id = request.user.id
            
            # Insert into ChargingStationOrder using raw SQL
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO myapp_chargingstationorder (charging_station_id, order_date, order_start, order_finish, user_id)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    [station_id, order_date, order_start, order_finish, user_id]
                )
            
            messages.success(request, 'Order scheduled successfully!')
            return redirect('order history')  # Replace with your success URL
        else:
            messages.error(request, 'Failed to schedule the charging station. Please correct the errors below.')
            print("*** Form Errors ***")
            print(form.errors)  # Print form errors for debugging
    else:
        initial_data = {
            'charging_station': station_id,
        }
        form = ChargingStationOrderForm(initial=initial_data)

    # Debug information
    print("*** POST Data 2 ***")
    print(request.POST)
    print("*** Printing form ****")
    print(form)
    print("*** Printing Station ****")
    print(station)
    print("*** Printing Station ID ****")
    print(station_id)
    print("*** Printing Current time and date ****")
    print(timezone.now().time(), timezone.now().date())

    return render(request, 'schedule_station.html', {'form': form, 'station': station})



@login_required
def create_order(request, station_id):
    if request.method == 'POST':
        form = ChargingStationOrderForm(request.POST)
        print(request.POST)
        if form.is_valid():
            # Save the form data to the database
            order = form.save(commit=False)
            order.charging_station_id = station_id  # Assign the station_id from URL
            order.user_id = request.user.id  # Assign the ordering user's ID
            order.save()
            return redirect('login/home/')  # Replace with your success URL
            
    else:
        form = ChargingStationOrderForm(initial={'user': request.user.id})  # Initialize user field

    return render(request, 'schedule_station.html', {'form': form})





"""
def schedule_station(request, station_id):
    station = ChargingStation.objects.get(pk=station_id)
    
    if request.method == 'POST':
        form = ChargingStationOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.charging_station = station
            order.user = request.user
            try:
                order.clean()
                order.save()
                messages.success(request, "Charging slot booked successfully!")
                return redirect('charging_stations_list')
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = ChargingStationOrderForm()

    context = {
        'station': station,
        'form': form,
    }
    return render(request, 'schedule_station.html', context)


def get_available_times(station, order_date):
    available_hours = []
    start_time = station.working_hours_start
    end_time = station.working_hours_finish

    # Create a list of potential time slots throughout the working hours
    current_time = start_time
    while current_time < end_time:
        next_time = (datetime.combine(datetime.today(), current_time) + timedelta(minutes=30)).time()
        available_hours.append({
            'start': current_time.strftime('%H:%M'),
            'end': next_time.strftime('%H:%M')
        })
        current_time = next_time

    # Filter out booked time slots based on existing orders
    existing_orders = ChargingStationOrder.objects.filter(
        charging_station=station, order_date=order_date
    )
    booked_times = [(order.order_start.time(), order.order_finish.time()) for order in existing_orders]

    filtered_hours = []
    for hour in available_hours:
        start_time = datetime.strptime(hour['start'], '%H:%M').time()
        end_time = datetime.strptime(hour['end'], '%H:%M').time()
        if not any(conflict_start <= start_time < conflict_end or conflict_start < end_time <= conflict_end for conflict_start, conflict_end in booked_times):
            filtered_hours.append(hour)

    return filtered_hours

"""






        
