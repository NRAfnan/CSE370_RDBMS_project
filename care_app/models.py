from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class ElderProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    guardian = models.ForeignKey(User, on_delete=models.CASCADE, related_name='elders')
    full_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    medical_conditions = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    blood_type = models.CharField(max_length=5, blank=True)
    emergency_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name
    
    @property
    def name(self):
        """Property to provide backward compatibility with templates using elder.name"""
        return self.full_name
    
    @property
    def age(self):
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None

class Medication(models.Model):
    MEDICATION_TYPE_CHOICES = [
        ('PILL', 'Pill'),
        ('LIQUID', 'Liquid'),
        ('INJECTION', 'Injection'),
        ('INHALER', 'Inhaler'),
        ('TOPICAL', 'Topical'),
        ('OTHER', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    medication_type = models.CharField(max_length=20, choices=MEDICATION_TYPE_CHOICES, default='PILL')
    strength = models.CharField(max_length=50, blank=True)
    manufacturer = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class MedicationSchedule(models.Model):
    FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('TWICE_DAILY', 'Twice Daily'),
        ('THRICE_DAILY', 'Three Times Daily'),
        ('WEEKLY', 'Weekly'),
        ('AS_NEEDED', 'As Needed'),
        ('CUSTOM', 'Custom'),
    ]
    
    elder = models.ForeignKey(ElderProfile, on_delete=models.CASCADE, related_name='medication_schedules')
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    dosage = models.CharField(max_length=50)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='DAILY')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    time_1 = models.TimeField(blank=True, null=True)
    time_2 = models.TimeField(blank=True, null=True)
    time_3 = models.TimeField(blank=True, null=True)
    instructions = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.medication.name} for {self.elder.full_name}"

class MedicationLog(models.Model):
    schedule = models.ForeignKey(MedicationSchedule, on_delete=models.CASCADE, related_name='logs')
    taken_at = models.DateTimeField(auto_now_add=True)
    taken_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    was_skipped = models.BooleanField(default=False)
    skip_reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.schedule.medication.name} taken at {self.taken_at}"

class Appointment(models.Model):
    APPOINTMENT_TYPE_CHOICES = [
        ('DOCTOR', 'Doctor Visit'),
        ('THERAPY', 'Physical Therapy'),
        ('LAB', 'Lab Work'),
        ('SPECIALIST', 'Specialist Consultation'),
        ('FOLLOW_UP', 'Follow-up'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('RESCHEDULED', 'Rescheduled'),
    ]
    
    elder = models.ForeignKey(ElderProfile, on_delete=models.CASCADE, related_name='appointments')
    title = models.CharField(max_length=100)
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPE_CHOICES, default='DOCTOR')
    appointment_date = models.DateTimeField()
    duration = models.IntegerField(help_text='Duration in minutes', default=30)
    location = models.TextField(blank=True)
    doctor_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    reminder_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.elder.full_name}"

class CareTask(models.Model):
    TASK_TYPE_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('ONE_TIME', 'One Time'),
        ('CUSTOM', 'Custom'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    elder = models.ForeignKey(ElderProfile, on_delete=models.CASCADE, related_name='care_tasks')
    title = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField()
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, default='DAILY')
    frequency = models.CharField(max_length=50, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_tasks')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title or 'Untitled Task'} ({self.status})"

class EmergencyContact(models.Model):
    RELATION_CHOICES = [
        ('SPOUSE', 'Spouse'),
        ('CHILD', 'Child'),
        ('SIBLING', 'Sibling'),
        ('FRIEND', 'Friend'),
        ('NEIGHBOR', 'Neighbor'),
        ('DOCTOR', 'Doctor'),
        ('OTHER', 'Other'),
    ]
    
    elder = models.ForeignKey(ElderProfile, on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=100)
    relation = models.CharField(max_length=20, choices=RELATION_CHOICES, default='OTHER')
    phone = models.CharField(max_length=20)
    phone_2 = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_primary = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_emergency_contacts')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_emergency_contacts')

    def __str__(self):
        return f"{self.name} - {self.relation}"
    
    def save(self, *args, **kwargs):
        # If this contact is being set as primary, unset other primary contacts for this elder
        if self.is_primary:
            EmergencyContact.objects.filter(
                elder=self.elder, 
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-is_primary', 'name']

class VitalsLog(models.Model):
    elder = models.ForeignKey(ElderProfile, on_delete=models.CASCADE, related_name='vitals_logs')
    recorded_at = models.DateTimeField(auto_now_add=True)
    blood_pressure_systolic = models.IntegerField(validators=[MinValueValidator(50), MaxValueValidator(300)], null=True, blank=True)
    blood_pressure_diastolic = models.IntegerField(validators=[MinValueValidator(30), MaxValueValidator(200)], null=True, blank=True)
    heart_rate = models.IntegerField(validators=[MinValueValidator(30), MaxValueValidator(200)], null=True, blank=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, validators=[MinValueValidator(90.0), MaxValueValidator(110.0)], null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    oxygen_saturation = models.IntegerField(validators=[MinValueValidator(70), MaxValueValidator(100)], null=True, blank=True)
    blood_sugar = models.IntegerField(validators=[MinValueValidator(20), MaxValueValidator(600)], null=True, blank=True)
    notes = models.TextField(blank=True)
    logged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Vitals {self.elder.full_name} @ {self.recorded_at}"
    
    @property
    def blood_pressure(self):
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            return f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}"
        return "N/A"

class IncidentReport(models.Model):
    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    INCIDENT_TYPE_CHOICES = [
        ('FALL', 'Fall'),
        ('MEDICATION_ERROR', 'Medication Error'),
        ('INJURY', 'Injury'),
        ('ILLNESS', 'Illness'),
        ('BEHAVIORAL', 'Behavioral Issue'),
        ('EQUIPMENT', 'Equipment Failure'),
        ('OTHER', 'Other'),
    ]
    
    elder = models.ForeignKey(ElderProfile, on_delete=models.CASCADE, related_name='incident_reports')
    incident_type = models.CharField(max_length=20, choices=INCIDENT_TYPE_CHOICES, default='OTHER')
    report_date = models.DateTimeField(auto_now_add=True)
    incident_date = models.DateTimeField()
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MEDIUM')
    location = models.CharField(max_length=200, blank=True)
    witnesses = models.TextField(blank=True)
    actions_taken = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_notes = models.TextField(blank=True)
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_resolved = models.BooleanField(default=False)
    resolved_date = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_incidents')

    def __str__(self):
        return f"{self.incident_type}: {self.elder.full_name}"

class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('MEDICATION', 'Medication Reminder'),
        ('APPOINTMENT', 'Appointment Reminder'),
        ('TASK', 'Task Reminder'),
        ('VITALS', 'Vitals Due'),
        ('INCIDENT', 'Incident Alert'),
        ('GENERAL', 'General'),
    ]
    
    elder = models.ForeignKey(ElderProfile, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES, default='GENERAL')
    message = models.TextField()
    created_at = models.DateTimeField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    read_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='read_notifications')
    priority = models.CharField(max_length=20, choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High')], default='MEDIUM')
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.notification_type}: {self.message[:20]}"

class UserProfile(models.Model):
    USER_TYPE_CHOICES = [
        ('ADMIN', 'Administrator'),
        ('CAREGIVER', 'Caregiver'),
        ('GUARDIAN', 'Guardian'),
        ('NURSE', 'Nurse'),
        ('DOCTOR', 'Doctor'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='CAREGIVER')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.user_type}"
