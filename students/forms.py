from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import User
from .models import Student
from courses.models import Class
import datetime

class StudentRegistrationForm(UserCreationForm):
    # Student Model Fields
    class_enrolled = forms.ModelChoiceField(
        queryset=None,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    admission_number = forms.CharField(max_length=20, required=False)
    roll_number = forms.CharField(max_length=20, required=False)
  #  section = forms.CharField(max_length=10, required=False)
    admission_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
   # category = forms.CharField(max_length=50, required=False)
    category = forms.ChoiceField(
        choices=Student.category.field.choices,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    father_name = forms.CharField(max_length=100, required=False)
    mother_name = forms.CharField(max_length=100, required=False)
    father_occupation = forms.CharField(max_length=100, required=False)
    mother_occupation = forms.CharField(max_length=100, required=False)
    parent_phone = forms.CharField(max_length=20, required=False)
    parent_email = forms.EmailField(required=False)
    emergency_contact = forms.CharField(max_length=20, required=False)
    
    blood_group = forms.CharField(max_length=5, required=False)
    allergies = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    medical_conditions = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    
    uses_transport = forms.BooleanField(required=False)
    transport_route = forms.CharField(max_length=100, required=False)
    bus_stop = forms.CharField(max_length=100, required=False)
    
    previous_school = forms.CharField(max_length=200, required=False)
    religion = forms.CharField(max_length=50, required=False)
    aadhaar_number = forms.CharField(max_length=20, required=False)
    nationality = forms.CharField(max_length=50, required=False)
    
    transfer_certificate = forms.FileField(required=False)
    birth_certificate = forms.FileField(required=False)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2',
                 'date_of_birth', 'gender', 'phone', 'address', 'profile_picture', 
                 'class_enrolled')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from courses.models import Class
        self.fields['class_enrolled'].queryset = Class.objects.all()
        
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'student'
        if commit:
            user.save()
            # Create student profile
            Student.objects.create(
                user=user,
                class_enrolled=self.cleaned_data['class_enrolled'],
                admission_number=self.cleaned_data.get('admission_number'),
                roll_number=self.cleaned_data.get('roll_number'),
                section=self.cleaned_data.get('section'),
                admission_date=self.cleaned_data.get('admission_date') or datetime.date.today(),
                category=self.cleaned_data.get('category'),
                father_name=self.cleaned_data.get('father_name'),
                mother_name=self.cleaned_data.get('mother_name'),
                father_occupation=self.cleaned_data.get('father_occupation'),
                mother_occupation=self.cleaned_data.get('mother_occupation'),
                parent_phone=self.cleaned_data.get('parent_phone'),
                parent_email=self.cleaned_data.get('parent_email'),
                emergency_contact=self.cleaned_data.get('emergency_contact'),
                blood_group=self.cleaned_data.get('blood_group'),
                allergies=self.cleaned_data.get('allergies'),
                medical_conditions=self.cleaned_data.get('medical_conditions'),
                uses_transport=self.cleaned_data.get('uses_transport'),
                transport_route=self.cleaned_data.get('transport_route'),
                bus_stop=self.cleaned_data.get('bus_stop'),
                previous_school=self.cleaned_data.get('previous_school'),
                religion=self.cleaned_data.get('religion'),
                aadhaar_number=self.cleaned_data.get('aadhaar_number'),
                nationality=self.cleaned_data.get('nationality'),
                transfer_certificate=self.cleaned_data.get('transfer_certificate'),
                birth_certificate=self.cleaned_data.get('birth_certificate')
            )
        return user

class StudentUpdateForm(forms.ModelForm):
    # User Fields
    username = forms.CharField(required=True)
    email = forms.EmailField(required=False)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    gender = forms.ChoiceField(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], required=False)
    phone = forms.CharField(required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    section = forms.CharField(max_length=10, required=False)
    profile_picture = forms.ImageField(required=False)
    nationality = forms.CharField(max_length=50, required=False)

    class Meta:
        model = Student
        fields = '__all__'
        exclude = ['user', 'created_at', 'updated_at']
        widgets = {
            'admission_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'leaving_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'medical_conditions': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'allergies': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'leaving_reason': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate initial data from User instance
        if self.instance and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['date_of_birth'].initial = self.instance.user.date_of_birth
            self.fields['gender'].initial = self.instance.user.gender
            self.fields['phone'].initial = self.instance.user.phone
            self.fields['address'].initial = self.instance.user.address
            self.fields['section'].initial = self.instance.section
            self.fields['nationality'].initial = self.instance.nationality

        for field in self.fields.values():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect, forms.FileInput)):
                field.widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        student = super().save(commit=False)
        if commit:
            student.save()
            user = student.user
            user.username = self.cleaned_data['username']
            student.nationality = self.cleaned_data['nationality']
            student.section = self.cleaned_data['section']
            user.email = self.cleaned_data['email']
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.date_of_birth = self.cleaned_data['date_of_birth']
            user.gender = self.cleaned_data['gender']
            user.phone = self.cleaned_data['phone']
            user.address = self.cleaned_data['address']
            if self.cleaned_data.get('profile_picture'):
                user.profile_picture = self.cleaned_data['profile_picture']
            user.save()
            student.save()
        return student