from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    ElderProfile, Medication, MedicationSchedule, MedicationLog,
    Appointment, CareTask, EmergencyContact, VitalsLog,
    IncidentReport, Notification, UserProfile
)

@admin.register(ElderProfile)
class ElderProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'age', 'gender', 'guardian', 'blood_type', 'created_at', 'updated_at']
    list_filter = ['gender', 'blood_type', 'created_at', 'guardian']
    search_fields = ['full_name', 'medical_conditions', 'address', 'guardian__username', 'guardian__first_name', 'guardian__last_name']
    readonly_fields = ['created_at', 'updated_at', 'age']
    fieldsets = (
        ('Basic Information', {
            'fields': ('guardian', 'full_name', 'date_of_birth', 'gender')
        }),
        ('Contact Information', {
            'fields': ('address', 'phone', 'email')
        }),
        ('Medical Information', {
            'fields': ('medical_conditions', 'allergies', 'blood_type', 'emergency_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def age(self, obj):
        return obj.age if obj.age else 'N/A'
    age.short_description = 'Age'

@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'medication_type', 'strength', 'manufacturer', 'is_active']
    list_filter = ['medication_type', 'is_active', 'manufacturer']
    search_fields = ['name', 'description', 'strength', 'manufacturer']
    list_editable = ['is_active']

@admin.register(MedicationSchedule)
class MedicationScheduleAdmin(admin.ModelAdmin):
    list_display = ['elder', 'medication', 'dosage', 'frequency', 'start_date', 'end_date', 'is_active']
    list_filter = ['frequency', 'is_active', 'start_date', 'end_date', 'elder']
    search_fields = ['elder__full_name', 'medication__name', 'dosage']
    list_editable = ['is_active']
    date_hierarchy = 'start_date'
    fieldsets = (
        ('Schedule Information', {
            'fields': ('elder', 'medication', 'dosage', 'frequency', 'start_date', 'end_date')
        }),
        ('Timing', {
            'fields': ('time_1', 'time_2', 'time_3', 'instructions')
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )

@admin.register(MedicationLog)
class MedicationLogAdmin(admin.ModelAdmin):
    list_display = ['schedule', 'taken_at', 'taken_by', 'was_skipped']
    list_filter = ['was_skipped', 'taken_at', 'schedule__elder']
    search_fields = ['schedule__medication__name', 'schedule__elder__full_name', 'taken_by__username']
    readonly_fields = ['taken_at']
    date_hierarchy = 'taken_at'

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'elder', 'appointment_type', 'appointment_date', 'status', 'doctor_name']
    list_filter = ['appointment_type', 'status', 'appointment_date', 'elder']
    search_fields = ['title', 'elder__full_name', 'doctor_name', 'location', 'notes']
    list_editable = ['status']
    date_hierarchy = 'appointment_date'
    fieldsets = (
        ('Appointment Details', {
            'fields': ('elder', 'title', 'appointment_type', 'appointment_date', 'duration')
        }),
        ('Location & Contact', {
            'fields': ('location', 'doctor_name', 'phone')
        }),
        ('Additional Information', {
            'fields': ('notes', 'status', 'reminder_sent')
        })
    )

@admin.register(CareTask)
class CareTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'elder', 'task_type', 'priority', 'status', 'assigned_to', 'due_date']
    list_filter = ['task_type', 'priority', 'status', 'due_date', 'elder']
    search_fields = ['title', 'description', 'elder__full_name', 'assigned_to__username']
    list_editable = ['status', 'priority']
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Task Information', {
            'fields': ('elder', 'title', 'description', 'task_type', 'frequency')
        }),
        ('Assignment & Priority', {
            'fields': ('assigned_to', 'priority', 'due_date')
        }),
        ('Status & Completion', {
            'fields': ('status', 'completed_at', 'completed_by', 'notes')
        })
    )

@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'elder', 'relation', 'phone', 'is_primary']
    list_filter = ['relation', 'is_primary', 'elder']
    search_fields = ['name', 'elder__full_name', 'phone', 'email']
    list_editable = ['is_primary']
    fieldsets = (
        ('Contact Information', {
            'fields': ('elder', 'name', 'relation', 'phone', 'phone_2', 'email')
        }),
        ('Additional Details', {
            'fields': ('address', 'is_primary', 'notes')
        })
    )

@admin.register(VitalsLog)
class VitalsLogAdmin(admin.ModelAdmin):
    list_display = ['elder', 'recorded_at', 'blood_pressure', 'heart_rate', 'temperature', 'weight', 'logged_by']
    list_filter = ['recorded_at', 'elder', 'logged_by']
    search_fields = ['elder__full_name', 'notes']
    readonly_fields = ['recorded_at']
    date_hierarchy = 'recorded_at'
    fieldsets = (
        ('Vitals Information', {
            'fields': ('elder', 'blood_pressure_systolic', 'blood_pressure_diastolic', 'heart_rate', 'temperature')
        }),
        ('Additional Measurements', {
            'fields': ('weight', 'oxygen_saturation', 'blood_sugar')
        }),
        ('Notes & Logging', {
            'fields': ('notes', 'logged_by')
        })
    )
    
    def blood_pressure(self, obj):
        if obj.blood_pressure_systolic and obj.blood_pressure_diastolic:
            return f"{obj.blood_pressure_systolic}/{obj.blood_pressure_diastolic}"
        return "N/A"
    blood_pressure.short_description = 'Blood Pressure'

@admin.register(IncidentReport)
class IncidentReportAdmin(admin.ModelAdmin):
    list_display = ['incident_type', 'elder', 'incident_date', 'severity', 'is_resolved', 'reported_by']
    list_filter = ['incident_type', 'severity', 'is_resolved', 'incident_date', 'elder']
    search_fields = ['elder__full_name', 'description', 'location', 'reported_by__username']
    list_editable = ['is_resolved']
    date_hierarchy = 'incident_date'
    fieldsets = (
        ('Incident Details', {
            'fields': ('elder', 'incident_type', 'incident_date', 'description', 'severity')
        }),
        ('Location & Witnesses', {
            'fields': ('location', 'witnesses')
        }),
        ('Actions & Follow-up', {
            'fields': ('actions_taken', 'follow_up_required', 'follow_up_notes')
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolved_date', 'resolved_by')
        }),
        ('Reporting', {
            'fields': ('reported_by',)
        })
    )

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['notification_type', 'elder', 'message_preview', 'priority', 'is_read', 'created_at']
    list_filter = ['notification_type', 'priority', 'is_read', 'created_at']
    search_fields = ['message', 'elder__full_name']
    list_editable = ['is_read', 'priority']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def message_preview(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_type', 'phone', 'is_active', 'created_at']
    list_filter = ['user_type', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'phone']
    list_editable = ['is_active']
    readonly_fields = ['created_at']

# Customize admin site
admin.site.site_header = "Special Care Platform Administration"
admin.site.site_title = "Care Platform Admin"
admin.site.index_title = "Welcome to Special Care Platform Administration"
