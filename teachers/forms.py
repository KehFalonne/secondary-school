from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import User
from .models import Teacher
from django.contrib.auth.forms import UserChangeForm
import datetime

class TeacherRegistrationForm(UserCreationForm):
    employee_id = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': True})
    )
    qualification = forms.ChoiceField(
        choices=Teacher.QUALIFICATION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    specialization = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    designation = forms.ChoiceField(
        choices=Teacher.DESIGNATION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='Teacher'
    )
    joining_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=datetime.date.today
    )
    subjects = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '5'})
    )
    experience_years = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        initial=0
    )
    previous_school = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    pan_number = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    bank_account = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    bank_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    bank_branch = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    ifsc_code = forms.CharField(
        max_length=11,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    salary = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    salary_type = forms.ChoiceField(
        choices=[
            ('Monthly', 'Monthly'),
            ('Contract', 'Contract'),
            ('Hourly', 'Hourly')
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='Monthly'
    )
    is_class_teacher = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    class_teacher_of = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2',
                 'date_of_birth', 'gender', 'phone', 'address', 'profile_picture')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from courses.models import Subject, Class
        
        self.fields['subjects'].queryset = Subject.objects.all()
        self.fields['class_teacher_of'].queryset = Class.objects.all()
        
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect)):
                if 'class' not in field.widget.attrs:
                    field.widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'teacher'
        if commit:
            user.save()
            # Create teacher profile
            teacher = Teacher.objects.create(
                user=user,
                employee_id=self.cleaned_data.get('employee_id', ''),
                qualification=self.cleaned_data['qualification'],
                specialization=self.cleaned_data['specialization'],
                designation=self.cleaned_data['designation'],
                joining_date=self.cleaned_data['joining_date'],
                experience_years=self.cleaned_data.get('experience_years', 0),
                previous_school=self.cleaned_data.get('previous_school', ''),
                pan_number=self.cleaned_data.get('pan_number', '') or None,
                bank_account=self.cleaned_data.get('bank_account', ''),
                bank_name=self.cleaned_data.get('bank_name', ''),
                bank_branch=self.cleaned_data.get('bank_branch', ''),
                ifsc_code=self.cleaned_data.get('ifsc_code', ''),
                salary=self.cleaned_data.get('salary'),
                salary_type=self.cleaned_data.get('salary_type', 'Monthly'),
                is_class_teacher=self.cleaned_data.get('is_class_teacher', False),
                class_teacher_of=self.cleaned_data.get('class_teacher_of')
            )
            # Add subjects
            if self.cleaned_data.get('subjects'):
                teacher.subjects.set(self.cleaned_data['subjects'])
        return user
    
class TeacherUpdateForm(forms.ModelForm):
    # User fields from your User model
    username = forms.CharField(
        max_length=150, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        max_length=30, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=150, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    gender = forms.ChoiceField(
        choices=[
            ('', 'Select Gender'),
            ('Male', 'Male'),
            ('Female', 'Female'), 
            ('Other', 'Other')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    # Teacher fields (copy from your TeacherRegistrationForm)
    employee_id = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': True})
    )
    qualification = forms.ChoiceField(
        choices=Teacher.QUALIFICATION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    specialization = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    designation = forms.ChoiceField(
        choices=Teacher.DESIGNATION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='Teacher'
    )
    joining_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=datetime.date.today
    )
    subjects = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '5'})
    )
    experience_years = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        initial=0
    )
    previous_school = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    pan_number = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    bank_account = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    bank_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    bank_branch = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    ifsc_code = forms.CharField(
        max_length=11,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    salary = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    salary_type = forms.ChoiceField(
        choices=[
            ('Monthly', 'Monthly'),
            ('Contract', 'Contract'),
            ('Hourly', 'Hourly')
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='Monthly'
    )
    is_class_teacher = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    class_teacher_of = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    leaving_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    leaving_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
    )
    
    class Meta:
        model = Teacher
        exclude = ['user', 'created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from courses.models import Subject, Class
        
        self.fields['subjects'].queryset = Subject.objects.all()
        self.fields['class_teacher_of'].queryset = Class.objects.all()
        
        # Populate User fields if instance exists
        if self.instance and self.instance.user:
            user = self.instance.user
            self.fields['username'].initial = user.username
            self.fields['email'].initial = user.email
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['date_of_birth'].initial = user.date_of_birth
            self.fields['gender'].initial = user.gender
            self.fields['phone'].initial = user.phone
            self.fields['address'].initial = user.address
            self.fields['profile_picture'].initial = user.profile_picture
        
        # Apply CSS classes to all fields
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect)):
                if 'class' not in field.widget.attrs:
                    field.widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        teacher = super().save(commit=False)
        
        # Update User model
        if teacher.user:
            teacher.user.username = self.cleaned_data['username']
            teacher.user.email = self.cleaned_data['email']
            teacher.user.first_name = self.cleaned_data['first_name']
            teacher.user.last_name = self.cleaned_data['last_name']
            teacher.user.date_of_birth = self.cleaned_data.get('date_of_birth')
            teacher.user.gender = self.cleaned_data.get('gender')
            teacher.user.phone = self.cleaned_data.get('phone')
            teacher.user.address = self.cleaned_data.get('address')
            teacher.user.profile_picture = self.cleaned_data.get('profile_picture')
            teacher.user.save()
        
        if commit:
            teacher.save()
            self.save_m2m()  # Save many-to-many fields (subjects)
        
        return teacher