
from datetime import timezone
from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import connections, connection
from bootstrap_datepicker_plus.widgets import DatePickerInput
from datetime import time




class SignUpForm(UserCreationForm):
	email = forms.EmailField(label="", widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Email Address'}))
	first_name = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'First Name'}))
	last_name = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Last Name'}))

	class Meta:
		model = User
		fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

	def __init__(self, *args, **kwargs):
		super(SignUpForm, self).__init__(*args, **kwargs)

		self.fields['username'].widget.attrs['class'] = 'form-control'
		self.fields['username'].widget.attrs['placeholder'] = 'User Name'
		self.fields['username'].label = ''
		self.fields['username'].help_text = '<li span class="form-text text-muted"><small>Required: 150 characters or fewer. Letters, digits and @/./+/-/_ only.</small></span li>'

		self.fields['password1'].widget.attrs['class'] = 'form-control'
		self.fields['password1'].widget.attrs['placeholder'] = 'Password'
		self.fields['password1'].label = ''
		self.fields['password1'].help_text = '<ul class="form-text text-muted small"><li>Your password can\'t be too similar to your other personal information.</li><li>Your password must contain at least 8 characters.</li><li>Your password can\'t be a commonly used password.</li><li>Your password can\'t be entirely numeric.</li></ul>'

		self.fields['password2'].widget.attrs['class'] = 'form-control'
		self.fields['password2'].widget.attrs['placeholder'] = 'Confirm Password'
		self.fields['password2'].label = ''
		self.fields['password2'].help_text = '<li span class="form-text text-muted"><small>Enter the same password as before, for verification.</small></span li>'
		
def save(self, commit=True):
    user = super(SignUpForm, self).save(commit=False)
    user.email = self.cleaned_data['email']

    if commit:
        with connection.cursor() as cursor:
            # Save the user using SQL
            cursor.execute(
                """
                INSERT INTO auth_user (username, email, password, is_superuser, is_staff, is_active, date_joined)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                [user.username, user.email, user.password, False, False, True, timezone.now()]
            )

        # Fetch the user's ID after saving
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM auth_user
                WHERE username = %s
                """,
                [user.username]
            )
            user.id = cursor.fetchone()[0]

        # Create the associated Profile for the user
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO myapp_profile (user_id, max_walking_distance)
                VALUES (%s, %s)
                """,
                [user.id, 1000] 
            )

    return user



class RegisterUserForm(UserCreationForm):
	email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control'}))
	first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class':'form-control'}))
	last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class':'form-control'}))
	

	class Meta:
		model = User
		fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')


	def __init__(self, *args, **kwargs):
		super(RegisterUserForm, self).__init__(*args, **kwargs)

		self.fields['username'].widget.attrs['class'] = 'form-control'
		self.fields['password1'].widget.attrs['class'] = 'form-control'
		self.fields['password2'].widget.attrs['class'] = 'form-control'

class ChargingStationForm(forms.ModelForm):

	address = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Address'}))
	description =  forms.CharField(label="", max_length=200, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Write anything to describe your charging station'}))
    
	def	__init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['charger'].queryset = Charger.objects.all()

	class Meta:
		model = ChargingStation
		fields = ('address', 'charger', 'description')


class ChargingStationViewForm(forms.ModelForm):
    class Meta:
        model = ChargingStation
        fields = ['working_hours_start', 'working_hours_finish']

class ChargingStationUpdateForm(forms.Form):
    charging_station = forms.ModelChoiceField(queryset=None, empty_label=None)
    working_hours_start = forms.TimeField(widget=forms.TimeInput(attrs={'class': 'form-control datetimepicker-input'}))
    working_hours_finish = forms.TimeField(widget=forms.TimeInput(attrs={'class': 'form-control datetimepicker-input'}))

    def __init__(self, user, *args, **kwargs):
        super(ChargingStationUpdateForm, self).__init__(*args, **kwargs)
        self.fields['charging_station'].queryset = ChargingStation.objects.filter(user=user)



class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ['brand', 'car_model', 'plug_type']



class CarSelectionForm(forms.Form):
    car = forms.ChoiceField(label="Select a Car")

    def __init__(self, *args, **kwargs):
        super(CarSelectionForm, self).__init__(*args, **kwargs)
        self.fields['car'].choices = self.get_car_choices()

    def clean_car(self):
        car_id = self.cleaned_data.get('car')
        if car_id:
            return Car.objects.get(pk=car_id)
        else:
            raise forms.ValidationError("Please select a valid car.")

    def get_car_choices(self):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, brand || ' ' || car_model AS car_label
                FROM myapp_car
                """
            )
            cars = cursor.fetchall()

        return [(str(car[0]), car[1]) for car in cars]



class CSVUploadForm(forms.Form):
    csv_file = forms.FileField()



class DBSelectionForm(forms.Form):
	table = forms.ChoiceField(choices=[], label='Select a table')

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['table'].choices = self.get_table_choices()

	def get_table_choices(self):
		table_names = connections.introspection.table_names()
		#return [(table_name, table_name) for table_name in table_names]
		return table_names


class ExportForm(forms.Form):
    table = forms.ChoiceField(choices=[])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['table'].choices = self.get_table_choices()

    def get_table_choices(self):
        table_names = connections['default'].introspection.table_names()
        return [(table_name, table_name) for table_name in table_names]




class UserCarSelectionForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ['car_model']

    def __init__(self, user, *args, **kwargs):
        super(UserCarSelectionForm, self).__init__(*args, **kwargs)


        car_models = Car.objects.raw(
            '''
            SELECT DISTINCT car_model
            FROM myapp_usercars
            WHERE user_id = %s
            ''',
            [user.id]
        )

        # Set the queryset dynamically based on the SQL query results
        self.fields['car_model'].queryset = car_models



class ChargingStationSearchForm(forms.Form):
    address = forms.CharField(label='Address', max_length=100)
    car = forms.ModelChoiceField(
        queryset=None,
        empty_label='Select your car',
        label='')

    def __init__(self, user, *args, **kwargs):
        super(ChargingStationSearchForm, self).__init__(*args, **kwargs)
        self.fields['car'].queryset = user.usercars.cars.all().distinct()


class DeleteCarForm(forms.Form):
    car_id = forms.IntegerField(widget=forms.HiddenInput)


from django import forms
from datetime import datetime, timedelta

class ChargingStationScheduleForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ChargingStationScheduleForm, self).__init__(*args, **kwargs)
        
        # Calculate the time slots for the next 24 hours in 30-minute intervals
        start_time = datetime.now()
        end_time = start_time + timedelta(days=1)
        time_slots = [(start_time + timedelta(minutes=30 * i), start_time + timedelta(minutes=30 * (i + 1))) 
                      for i in range(int(((end_time - start_time).seconds) / 1800))]
        
        # Create choices for the time slots
        choices = [(slot[0], f"{slot[0].strftime('%Y-%m-%dT%H:%M')} - {slot[1].strftime('%Y-%m-%dT%H:%M')}") 
                   for slot in time_slots]
        
        # Set choices for the start and finish time fields
        self.fields['scheduled_time_start'].widget.choices = choices
        self.fields['scheduled_time_finish'].widget.choices = choices

    scheduled_time_start = forms.ChoiceField(
        label='Start Time',
        widget=forms.Select(),
    )
    scheduled_time_finish = forms.ChoiceField(
        label='Finish Time',
        widget=forms.Select(),
    )


    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('scheduled_time_start')
        finish_time = cleaned_data.get('scheduled_time_finish')

        if start_time and finish_time and start_time >= finish_time:
            raise forms.ValidationError('Finish time must be later than start time.')
        
class UpdateMaxWalkingDistanceForm(forms.Form):
    max_walking_distance = forms.FloatField(label='New Max Walking Distance', required=True)   



# forms.py
from django import forms
from .models import ChargingStationOrder

class ChargingStationOrderForm(forms.ModelForm):
    order_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    order_start = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
    )
    order_finish = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
    )

    class Meta:
        model = ChargingStationOrder
        fields = ['charging_station', 'order_date', 'order_start', 'order_finish']
        widgets = {
            'charging_station': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        












"""
class ChargingStationOrderForm(forms.ModelForm):
    class Meta:
        model = ChargingStationOrder
        fields = ['charging_station', 'order_date', 'order_start', 'order_finish']
        widgets = {
            'order_date': DatePickerInput(),  # DatePickerInput for date field
            'order_start': TimePickerInput(options={"showMeridian": True}),  # TimePickerInput for time fields
            'order_finish': TimePickerInput(options={"showMeridian": False}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order_start'].widget.attrs.update({'class': 'form-control datetimepicker-input'})
        self.fields['order_finish'].widget.attrs.update({'class': 'form-control datetimepicker-input'})
        self.fields['order_start'].input_formats = ['%I:%M %p', '%H:%M']
        self.fields['order_finish'].input_formats = ['%I:%M %p', '%H:%M']
"""




        

