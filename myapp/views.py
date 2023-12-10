import datetime, csv, os
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


def index(request):
    if request.user.is_authenticated:
        return redirect('login/home')
    else:   
        date = datetime.datetime.now()
        return render(request, "index.html", {"date": date})

def landing_page(request):
    return render(request, "LandingPage.html", {})



def choose_a_car(request):
    form = CarSelectionForm()

    if request.method == 'POST':
        form = CarSelectionForm(request.POST)
        if form.is_valid():
            selected_car_id = form.cleaned_data['car']

            # Assuming you have a UserCars model linking User and Car
            # Replace 'UserCars' with your actual model
            user_cars, created = UserCars.objects.get_or_create(user=request.user)

            # Associate the selected car with the user's profile using SQL
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO myapp_usercars_cars (usercars_id, car_id)
                    VALUES (%s, %s)
                    """,
                    [user_cars.id, selected_car_id.id]  # Use selected_car_id.id
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
            # Perform your deletion logic here
            car_id = form.cleaned_data['car_id']
            # Your deletion logic goes here
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
    charging_stations = ChargingStation.objects.all()
    charging_station_addresses = []

    if request.method == 'POST':
        form = ChargingStationSearchForm(request.user, request.POST)
        if form.is_valid():
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
                        charging_station_addresses = [station[1] for station in charging_stations]

    else:
        form = ChargingStationSearchForm(user=request.user)

    return render(request, 'home.html', {'form': form, 'charging_stations': charging_stations, 'charging_station_addresses': charging_station_addresses})


def new_user(request):
    return render(request, "NewUser.html", {})

#def get_messeges_query():
 #   return Messege.objects.raw("SELECT * FROM myapp_messege")
   
#def tamplate_quary():
#    name = "Banana"
#    age = 0
#    return Messege.objects.raw("SELECT * \
#                               FROM myapp_messege \
#                               WHARE user = %s AND age = %s",[name, age])

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


def order_history(request):
    return render(request, "OrderHistory.html", {})




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
    # Ensure the user is logged in

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
    try:
        charging_station = ChargingStation.objects.get(address=address)
        data = {
            'charger': charging_station.charger,
            'description': charging_station.description,
        }
        return JsonResponse(data)
    except ChargingStation.DoesNotExist:
        return JsonResponse({'error': 'Charging station not found'}, status=404)

from django.shortcuts import render
from .models import Media  # Import your Medias model

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




