from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import (
    ElderProfile, MedicationSchedule, Notification, Medication, 
    MedicationLog, Appointment, CareTask, EmergencyContact, 
    VitalsLog, IncidentReport, UserProfile
)
from .forms import (
    MedicationScheduleForm, MedicationForm, ElderForm, AppointmentForm,
    CareTaskForm, EmergencyContactForm, VitalsLogForm, IncidentReportForm,
    NotificationForm, UserProfileForm, UserRegistrationForm, QuickVitalsForm,
    SearchForm
)

@login_required
def dashboard(request):
    # Get user profile
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        user_profile = None
    
    # Get data based on user type
    if user_profile and user_profile.user_type == 'ADMIN':
        elders = ElderProfile.objects.all()
        total_elders = elders.count()
        upcoming_appointments = Appointment.objects.filter(
            appointment_date__gte=timezone.now(),
            status__in=['SCHEDULED', 'CONFIRMED']
        ).order_by('appointment_date')[:5]
        pending_tasks = CareTask.objects.filter(status='PENDING').order_by('priority', 'due_date')[:10]
        recent_incidents = IncidentReport.objects.filter(is_resolved=False).order_by('-incident_date')[:5]
    else:
        # For caregivers, show only assigned elders
        elders = ElderProfile.objects.filter(guardian=request.user)
        total_elders = elders.count()
        upcoming_appointments = Appointment.objects.filter(
            elder__in=elders,
            appointment_date__gte=timezone.now(),
            status__in=['SCHEDULED', 'CONFIRMED']
        ).order_by('appointment_date')[:5]
        pending_tasks = CareTask.objects.filter(
            elder__in=elders,
            status='PENDING'
        ).order_by('priority', 'due_date')[:10]
        recent_incidents = IncidentReport.objects.filter(
            elder__in=elders,
            is_resolved=False
        ).order_by('-incident_date')[:5]
    
    # Get notifications
    notifications = Notification.objects.filter(
        Q(elder__in=elders) | Q(elder__isnull=True),
        is_read=False
    ).order_by('-created_at')[:10]
    
    # Get today's medication schedules
    today = timezone.now().date()
    today_medications = MedicationSchedule.objects.filter(
        elder__in=elders,
        is_active=True,
        start_date__lte=today
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=today)
    )
    
    # Get vitals due today
    vitals_due = []
    for elder in elders:
        last_vitals = VitalsLog.objects.filter(elder=elder).order_by('-recorded_at').first()
        if not last_vitals or (today - last_vitals.recorded_at.date()).days >= 7:
            vitals_due.append(elder)
    
    context = {
        'elders': elders,
        'total_elders': total_elders,
        'upcoming_appointments': upcoming_appointments,
        'pending_tasks': pending_tasks,
        'recent_incidents': recent_incidents,
        'notifications': notifications,
        'today_medications': today_medications,
        'vitals_due': vitals_due,
        'user_profile': user_profile,
    }
    return render(request, 'dashboard.html', context)

@login_required
def elder_list(request):
    search_form = SearchForm(request.GET)
    query = request.GET.get('query', '')
    category = request.GET.get('category', 'all')
    
    try:
        user_profile = request.user.profile
        if user_profile and user_profile.user_type == 'ADMIN':
            elders = ElderProfile.objects.all()
        else:
            elders = ElderProfile.objects.filter(guardian=request.user)
    except UserProfile.DoesNotExist:
        elders = ElderProfile.objects.filter(guardian=request.user)
    
    if query:
        if category == 'elders' or category == 'all':
            elders = elders.filter(
                Q(full_name__icontains=query) |
                Q(medical_conditions__icontains=query) |
                Q(address__icontains=query)
            )
    
    context = {
        'elders': elders,
        'search_form': search_form,
        'query': query,
    }
    return render(request, 'elder_list.html', context)

@login_required
def elder_detail(request, elder_id):
    elder = get_object_or_404(ElderProfile, pk=elder_id)
    
    # Check if user has access to this elder
    try:
        user_profile = request.user.profile
        if user_profile and user_profile.user_type != 'ADMIN' and elder.guardian != request.user:
            messages.error(request, "You don't have permission to view this elder's details.")
            return redirect('elder_list')
    except UserProfile.DoesNotExist:
        if elder.guardian != request.user:
            messages.error(request, "You don't have permission to view this elder's details.")
            return redirect('elder_list')
    
    # Get related data
    medications = MedicationSchedule.objects.filter(elder=elder, is_active=True)
    appointments = Appointment.objects.filter(elder=elder).order_by('-appointment_date')[:10]
    care_tasks = CareTask.objects.filter(elder=elder).order_by('-created_at')[:10]
    emergency_contacts = EmergencyContact.objects.filter(elder=elder)
    recent_vitals = VitalsLog.objects.filter(elder=elder).order_by('-recorded_at')[:5]
    recent_incidents = IncidentReport.objects.filter(elder=elder).order_by('-incident_date')[:5]
    
    context = {
        'elder': elder,
        'medications': medications,
        'appointments': appointments,
        'care_tasks': care_tasks,
        'emergency_contacts': emergency_contacts,
        'recent_vitals': recent_vitals,
        'recent_incidents': recent_incidents,
    }
    return render(request, 'elder_detail.html', context)

@login_required
def elder_add(request):
    if request.method == 'POST':
        form = ElderForm(request.POST)
        if form.is_valid():
            elder = form.save(commit=False)
            elder.created_at = timezone.now()
            elder.updated_at = timezone.now()
            elder.save()
            messages.success(request, f'Elder profile for {elder.full_name} created successfully!')
            return redirect('elder_detail', elder_id=elder.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ElderForm(initial={'guardian': request.user})
    
    context = {'form': form, 'title': 'Add New Elder'}
    return render(request, 'elder_form.html', context)

@login_required
def elder_edit(request, elder_id):
    elder = get_object_or_404(ElderProfile, pk=elder_id)
    
    # Check permissions
    try:
        user_profile = request.user.profile
        if user_profile and user_profile.user_type != 'ADMIN' and elder.guardian != request.user:
            messages.error(request, "You don't have permission to edit this elder's profile.")
            return redirect('elder_detail', elder_id=elder.pk)
    except UserProfile.DoesNotExist:
        if elder.guardian != request.user:
            messages.error(request, "You don't have permission to edit this elder's profile.")
            return redirect('elder_detail', elder_id=elder.pk)
    
    if request.method == 'POST':
        form = ElderForm(request.POST, instance=elder)
        if form.is_valid():
            form.save()
            messages.success(request, f'Elder profile for {elder.full_name} updated successfully!')
            return redirect('elder_detail', elder_id=elder.pk)
    else:
        form = ElderForm(instance=elder)
    
    context = {'form': form, 'title': f'Edit {elder.full_name}', 'elder': elder}
    return render(request, 'elder_form.html', context)

@login_required
def medication_list(request, elder_id=None):
    if elder_id:
        elder = get_object_or_404(ElderProfile, pk=elder_id)
        medications = Medication.objects.filter(medicationschedule__elder=elder).distinct()
        elders = [elder]
    else:
        elder = None
        try:
            user_profile = request.user.profile
            if user_profile and user_profile.user_type == 'ADMIN':
                medications = Medication.objects.all()
                elders = ElderProfile.objects.all()
            else:
                elders = ElderProfile.objects.filter(guardian=request.user)
                medications = Medication.objects.filter(medicationschedule__elder__in=elders).distinct()
        except UserProfile.DoesNotExist:
            elders = ElderProfile.objects.filter(guardian=request.user)
            medications = Medication.objects.filter(medicationschedule__elder__in=elders).distinct()
    
    context = {'elder': elder, 'medications': medications, 'elders': elders}
    return render(request, 'medication_list.html', context)

@login_required
def medication_add(request):
    if request.method == 'POST':
        form = MedicationForm(request.POST)
        if form.is_valid():
            medication = form.save()
            messages.success(request, f'Medication {medication.name} added successfully!')
            return redirect('medication_list')
    else:
        form = MedicationForm()
        elder_id = request.GET.get('elder_id')
        if elder_id:
            form.fields['elder'].initial = elder_id
    
    context = {'form': form, 'title': 'Add New Medication'}
    return render(request, 'medication_form.html', context)

@login_required
def medication_edit(request, medication_id):
    medication = get_object_or_404(Medication, pk=medication_id)
    
    if request.method == 'POST':
        form = MedicationForm(request.POST, instance=medication)
        if form.is_valid():
            form.save()
            messages.success(request, f'Medication {medication.name} updated successfully!')
            return redirect('medication_list')
    else:
        form = MedicationForm(instance=medication)
    
    context = {'form': form, 'medication': medication, 'title': 'Edit Medication'}
    return render(request, 'medication_form.html', context)

@login_required
def medication_delete(request, medication_id):
    medication = get_object_or_404(Medication, pk=medication_id)
    
    if request.method == 'POST':
        medication.delete()
        messages.success(request, f'Medication {medication.name} deleted successfully!')
        return redirect('medication_list')
    
    context = {'medication': medication, 'title': 'Delete Medication'}
    return render(request, 'medication_confirm_delete.html', context)

@login_required
def medication_log_add(request):
    if request.method == 'POST':
        form = MedicationLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.taken_by = request.user
            log.save()
            messages.success(request, 'Medication log added successfully!')
            return redirect('medication_list')
    else:
        form = MedicationLogForm()
        medication_id = request.GET.get('medication')
        if medication_id:
            form.fields['schedule'].queryset = MedicationSchedule.objects.filter(medication_id=medication_id)
    
    context = {'form': form, 'title': 'Add Medication Log'}
    return render(request, 'medication_log_form.html', context)

@login_required
def med_schedule_add(request):
    if request.method == 'POST':
        form = MedicationScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save()
            messages.success(request, f'Medication schedule for {schedule.medication.name} created successfully!')
            return redirect('elder_detail', elder_id=schedule.elder.pk)
    else:
        elder_id = request.GET.get('elder_id')
        if elder_id:
            form = MedicationScheduleForm(initial={'elder': elder_id})
        else:
            form = MedicationScheduleForm()
    
    context = {'form': form, 'title': 'Add Medication Schedule'}
    return render(request, 'medication_schedule_form.html', context)

@login_required
def medication_log(request, schedule_id):
    schedule = get_object_or_404(MedicationSchedule, pk=schedule_id)
    
    if request.method == 'POST':
        form = MedicationLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.schedule = schedule
            log.taken_by = request.user
            log.save()
            
            # Create notification if medication was skipped
            if log.was_skipped:
                Notification.objects.create(
                    elder=schedule.elder,
                    notification_type='MEDICATION',
                    message=f'Medication {schedule.medication.name} was skipped. Reason: {log.skip_reason}',
                    priority='HIGH'
                )
            
            messages.success(request, 'Medication log updated successfully!')
            return redirect('elder_detail', elder_id=schedule.elder.pk)
    else:
        form = MedicationLogForm()
    
    context = {'form': form, 'schedule': schedule, 'title': 'Log Medication'}
    return render(request, 'medication_log_form.html', context)

@login_required
def appointment_list(request, elder_id=None):
    if elder_id:
        elder = get_object_or_404(ElderProfile, pk=elder_id)
        appointments = Appointment.objects.filter(elder=elder).order_by('-appointment_date')
    else:
        elder = None
        try:
            user_profile = request.user.profile
            if user_profile and user_profile.user_type == 'ADMIN':
                appointments = Appointment.objects.all().order_by('-appointment_date')
            else:
                elders = ElderProfile.objects.filter(guardian=request.user)
                appointments = Appointment.objects.filter(elder__in=elders).order_by('-appointment_date')
        except UserProfile.DoesNotExist:
            elders = ElderProfile.objects.filter(guardian=request.user)
            appointments = Appointment.objects.filter(elder__in=elders).order_by('-appointment_date')
    
    context = {'appointments': appointments, 'elder': elder}
    return render(request, 'appointment_list.html', context)

@login_required
def appointment_add(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.created_at = timezone.now()
            appointment.save()
            messages.success(request, f'Appointment "{appointment.title}" scheduled successfully!')
            return redirect('appointment_list')
    else:
        elder_id = request.GET.get('elder_id')
        if elder_id:
            form = AppointmentForm(initial={'elder': elder_id})
        else:
            form = AppointmentForm()
    
    context = {'form': form, 'title': 'Schedule Appointment'}
    return render(request, 'appointment_form.html', context)

@login_required
def appointment_edit(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            appointment = form.save(commit=False)
            if not appointment.created_at:
                appointment.created_at = timezone.now()
            appointment.save()
            messages.success(request, f'Appointment "{appointment.title}" updated successfully!')
            return redirect('appointment_list')
    else:
        form = AppointmentForm(instance=appointment)
    
    context = {'form': form, 'appointment': appointment, 'title': 'Edit Appointment'}
    return render(request, 'appointment_form.html', context)

@login_required
def appointment_delete(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    
    if request.method == 'POST':
        appointment.delete()
        messages.success(request, f'Appointment "{appointment.title}" deleted successfully!')
        return redirect('appointment_list')
    
    context = {'appointment': appointment, 'title': 'Delete Appointment'}
    return render(request, 'appointment_confirm_delete.html', context)

@login_required
def care_task_list(request, elder_id=None):
    if elder_id:
        elder = get_object_or_404(ElderProfile, pk=elder_id)
        tasks = CareTask.objects.filter(elder=elder).order_by('-created_at')
    else:
        elder = None
        try:
            user_profile = request.user.profile
            if user_profile and user_profile.user_type == 'ADMIN':
                tasks = CareTask.objects.all().order_by('-created_at')
            else:
                elders = ElderProfile.objects.filter(guardian=request.user)
                tasks = CareTask.objects.filter(elder__in=elders).order_by('-created_at')
        except UserProfile.DoesNotExist:
            elders = ElderProfile.objects.filter(guardian=request.user)
            tasks = CareTask.objects.filter(elder__in=elders).order_by('-created_at')
    
    context = {'tasks': tasks, 'elder': elder}
    return render(request, 'care_task_list.html', context)

@login_required
def care_task_add(request):
    if request.method == 'POST':
        form = CareTaskForm(request.POST)
        if form.is_valid():
            task = form.save()
            messages.success(request, f'Care task "{task.title}" created successfully!')
            return redirect('care_task_list')
    else:
        elder_id = request.GET.get('elder_id')
        if elder_id:
            form = CareTaskForm(initial={'elder': elder_id})
        else:
            form = CareTaskForm()
    
    context = {'form': form, 'title': 'Create Care Task'}
    return render(request, 'care_task_form.html', context)

@login_required
def care_task_edit(request, task_id):
    task = get_object_or_404(CareTask, pk=task_id)
    
    if request.method == 'POST':
        form = CareTaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, f'Task "{task.title}" updated successfully!')
            return redirect('care_task_list')
    else:
        form = CareTaskForm(instance=task)
    
    context = {'form': form, 'task': task, 'title': 'Edit Care Task'}
    return render(request, 'care_task_form.html', context)

@login_required
def care_task_delete(request, task_id):
    task = get_object_or_404(CareTask, pk=task_id)
    
    if request.method == 'POST':
        task.delete()
        messages.success(request, f'Task "{task.title}" deleted successfully!')
        return redirect('care_task_list')
    
    context = {'task': task, 'title': 'Delete Care Task'}
    return render(request, 'care_task_confirm_delete.html', context)

@login_required
def care_task_complete(request, task_id):
    task = get_object_or_404(CareTask, pk=task_id)
    
    # Check permissions
    try:
        user_profile = request.user.profile
        if user_profile and user_profile.user_type != 'ADMIN' and task.elder.guardian != request.user:
            messages.error(request, "You don't have permission to complete this task.")
            return redirect('care_task_list')
    except UserProfile.DoesNotExist:
        if task.elder.guardian != request.user:
            messages.error(request, "You don't have permission to complete this task.")
            return redirect('care_task_list')
    
    if request.method == 'POST':
        task.status = 'COMPLETED'
        task.completed_at = timezone.now()
        task.completed_by = request.user
        task.save()
        messages.success(request, f'Task "{task.title}" marked as completed!')
        return redirect('care_task_list')
    
    context = {'task': task}
    return render(request, 'care_task_complete.html', context)

@login_required
def emergency_contacts(request, elder_id):
    elder = get_object_or_404(ElderProfile, pk=elder_id)
    contacts = EmergencyContact.objects.filter(elder=elder).select_related('created_by', 'updated_by')
    
    # Get contact statistics
    total_contacts = contacts.count()
    primary_contacts = contacts.filter(is_primary=True).count()
    recent_updates = contacts.filter(updated_at__gte=timezone.now() - timedelta(days=7)).count()
    
    context = {
        'elder': elder, 
        'contacts': contacts,
        'total_contacts': total_contacts,
        'primary_contacts': primary_contacts,
        'recent_updates': recent_updates
    }
    return render(request, 'emergency_contacts.html', context)

@login_required
def emergency_contact_add(request, elder_id):
    elder = get_object_or_404(ElderProfile, pk=elder_id)
    
    if request.method == 'POST':
        form = EmergencyContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.elder = elder
            contact.created_by = request.user
            contact.updated_by = request.user
            
            # Validate primary contact uniqueness
            if contact.is_primary:
                existing_primary = EmergencyContact.objects.filter(
                    elder=elder, 
                    is_primary=True
                ).first()
                if existing_primary:
                    messages.warning(request, f'Primary contact already exists ({existing_primary.name}). This contact will be set as primary instead.')
            
            contact.save()
            
            # Create notification for contact addition
            Notification.objects.create(
                elder=elder,
                notification_type='GENERAL',
                message=f'New emergency contact added: {contact.name} ({contact.relation})',
                priority='MEDIUM'
            )
            
            messages.success(request, f'Emergency contact {contact.name} added successfully!')
            return redirect('emergency_contacts', elder_id=elder.pk)
    else:
        form = EmergencyContactForm()
    
    context = {'form': form, 'elder': elder, 'title': 'Add Emergency Contact'}
    return render(request, 'emergency_contact_form.html', context)

@login_required
def emergency_contact_edit(request, contact_id):
    contact = get_object_or_404(EmergencyContact, pk=contact_id)
    
    if request.method == 'POST':
        form = EmergencyContactForm(request.POST, instance=contact)
        if form.is_valid():
            # Store old values for comparison
            old_name = contact.name
            old_phone = contact.phone
            old_is_primary = contact.is_primary
            
            contact = form.save(commit=False)
            contact.updated_by = request.user
            contact.save()
            
            # Create notification for significant changes
            changes = []
            if old_name != contact.name:
                changes.append(f"name from '{old_name}' to '{contact.name}'")
            if old_phone != contact.phone:
                changes.append(f"phone number from '{old_phone}' to '{contact.phone}'")
            if old_is_primary != contact.is_primary:
                changes.append("primary contact status")
            
            if changes:
                Notification.objects.create(
                    elder=contact.elder,
                    notification_type='GENERAL',
                    message=f'Emergency contact updated: {", ".join(changes)}',
                    priority='MEDIUM'
                )
            
            messages.success(request, f'Emergency contact {contact.name} updated successfully!')
            return redirect('emergency_contacts', elder_id=contact.elder.pk)
    else:
        form = EmergencyContactForm(instance=contact)
    
    context = {'form': form, 'contact': contact, 'title': 'Edit Emergency Contact'}
    return render(request, 'emergency_contact_form.html', context)

@login_required
def emergency_contact_delete(request, contact_id):
    contact = get_object_or_404(EmergencyContact, pk=contact_id)
    
    if request.method == 'POST':
        # Create notification before deletion
        Notification.objects.create(
            elder=contact.elder,
            notification_type='GENERAL',
            message=f'Emergency contact deleted: {contact.name} ({contact.relation})',
            priority='HIGH'
        )
        
        contact_name = contact.name
        elder_id = contact.elder.pk
        contact.delete()
        
        messages.success(request, f'Emergency contact {contact_name} deleted successfully!')
        return redirect('emergency_contacts', elder_id=elder_id)
    
    context = {'contact': contact, 'title': 'Delete Emergency Contact'}
    return render(request, 'emergency_contact_confirm_delete.html', context)

@login_required
def vitals_list(request, elder_id=None):
    search_form = SearchForm(request.GET)
    query = request.GET.get('query', '')
    category = request.GET.get('category', 'all')
    
    if elder_id:
        elder = get_object_or_404(ElderProfile, pk=elder_id)
        vitals = VitalsLog.objects.filter(elder=elder).order_by('-recorded_at')
        elders = [elder]
    else:
        elder = None
        try:
            user_profile = request.user.profile
            if user_profile and user_profile.user_type == 'ADMIN':
                vitals = VitalsLog.objects.all().order_by('-recorded_at')
                elders = ElderProfile.objects.all()
            else:
                elders = ElderProfile.objects.filter(guardian=request.user)
                vitals = VitalsLog.objects.filter(elder__in=elders).order_by('-recorded_at')
        except UserProfile.DoesNotExist:
            elders = ElderProfile.objects.filter(guardian=request.user)
            vitals = VitalsLog.objects.filter(elder__in=elders).order_by('-recorded_at')
    
    # Apply search filter if query is provided
    if query:
        vitals = vitals.filter(
            Q(elder__full_name__icontains=query) |
            Q(notes__icontains=query) |
            Q(blood_pressure_systolic__icontains=query) |
            Q(blood_pressure_diastolic__icontains=query) |
            Q(heart_rate__icontains=query) |
            Q(temperature__icontains=query) |
            Q(weight__icontains=query) |
            Q(blood_sugar__icontains=query) |
            Q(oxygen_saturation__icontains=query)
        )
    
    context = {'elder': elder, 'vitals': vitals, 'elders': elders, 'search_form': search_form, 'query': query}
    return render(request, 'vitals_list.html', context)

@login_required
def vitals_add(request, elder_id=None):
    if elder_id:
        elder = get_object_or_404(ElderProfile, pk=elder_id)
    else:
        elder = None
    
    if request.method == 'POST':
        form = VitalsLogForm(request.POST)
        if form.is_valid():
            vitals = form.save(commit=False)
            if elder:
                vitals.elder = elder
            vitals.logged_by = request.user
            vitals.save()
            messages.success(request, 'Vitals logged successfully!')
            if elder:
                return redirect('vitals_list', elder_id=elder.pk)
            else:
                return redirect('vitals_list')
    else:
        form = VitalsLogForm()
        if elder:
            form.fields['elder'].initial = elder
    
    context = {'form': form, 'elder': elder, 'title': 'Log Vitals'}
    return render(request, 'vitals_form.html', context)

@login_required
def vitals_edit(request, vital_id):
    vital = get_object_or_404(VitalsLog, pk=vital_id)
    
    if request.method == 'POST':
        form = VitalsLogForm(request.POST, instance=vital)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vitals updated successfully!')
            return redirect('vitals_list')
    else:
        form = VitalsLogForm(instance=vital)
    
    context = {'form': form, 'vital': vital, 'title': 'Edit Vitals'}
    return render(request, 'vitals_form.html', context)

@login_required
def vitals_delete(request, vital_id):
    vital = get_object_or_404(VitalsLog, pk=vital_id)
    
    if request.method == 'POST':
        vital.delete()
        messages.success(request, 'Vitals deleted successfully!')
        return redirect('vitals_list')
    
    context = {'vital': vital, 'title': 'Delete Vitals'}
    return render(request, 'vitals_confirm_delete.html', context)

@login_required
def vitals_detail(request, vital_id):
    vital = get_object_or_404(VitalsLog, pk=vital_id)
    
    # Check permissions
    try:
        user_profile = request.user.profile
        if user_profile and user_profile.user_type != 'ADMIN' and vital.elder.guardian != request.user:
            messages.error(request, "You don't have permission to view this vital signs record.")
            return redirect('vitals_list')
    except UserProfile.DoesNotExist:
        if vital.elder.guardian != request.user:
            messages.error(request, "You don't have permission to view this vital signs record.")
            return redirect('vitals_list')
    
    context = {'vital': vital}
    return render(request, 'vitals_detail.html', context)

@login_required
def quick_vitals(request, elder_id):
    elder = get_object_or_404(ElderProfile, pk=elder_id)
    
    if request.method == 'POST':
        form = QuickVitalsForm(request.POST)
        if form.is_valid():
            vitals = VitalsLog()
            vitals.elder = elder
            vitals.logged_by = request.user
            
            # Only save fields that have values
            for field_name, value in form.cleaned_data.items():
                if value:
                    setattr(vitals, field_name, value)
            
            vitals.save()
            messages.success(request, 'Vitals logged successfully!')
            return redirect('elder_detail', elder_id=elder.pk)
    else:
        form = QuickVitalsForm()
    
    context = {'form': form, 'elder': elder, 'title': 'Quick Vitals Log'}
    return render(request, 'quick_vitals.html', context)

@login_required
def incident_list(request, elder_id=None):
    if elder_id:
        elder = get_object_or_404(ElderProfile, pk=elder_id)
        incidents = IncidentReport.objects.filter(elder=elder).order_by('-incident_date')
    else:
        elder = None
        try:
            user_profile = request.user.profile
            if user_profile and user_profile.user_type == 'ADMIN':
                incidents = IncidentReport.objects.all().order_by('-incident_date')
            else:
                elders = ElderProfile.objects.filter(guardian=request.user)
                incidents = IncidentReport.objects.filter(elder__in=elders).order_by('-incident_date')
        except UserProfile.DoesNotExist:
            elders = ElderProfile.objects.filter(guardian=request.user)
            incidents = IncidentReport.objects.filter(elder__in=elders).order_by('-incident_date')
    
    context = {'incidents': incidents, 'elder': elder}
    return render(request, 'incident_list.html', context)

@login_required
def incident_add(request):
    if request.method == 'POST':
        form = IncidentReportForm(request.POST)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.reported_by = request.user
            incident.save()
            
            # Create notification
            Notification.objects.create(
                elder=incident.elder,
                notification_type='INCIDENT',
                message=f'New incident reported: {incident.incident_type} - {incident.description[:50]}...',
                priority='HIGH'
            )
            
            messages.success(request, 'Incident report created successfully!')
            return redirect('incident_list')
    else:
        elder_id = request.GET.get('elder_id')
        if elder_id:
            form = IncidentReportForm(initial={'elder': elder_id})
        else:
            form = IncidentReportForm()
    
    context = {'form': form, 'title': 'Report Incident'}
    return render(request, 'incident_form.html', context)

@login_required
def incident_edit(request, incident_id):
    incident = get_object_or_404(IncidentReport, pk=incident_id)
    
    if request.method == 'POST':
        form = IncidentReportForm(request.POST, instance=incident)
        if form.is_valid():
            form.save()
            messages.success(request, f'Incident report updated successfully!')
            return redirect('incident_list')
    else:
        form = IncidentReportForm(instance=incident)
    
    context = {'form': form, 'incident': incident, 'title': 'Edit Incident Report'}
    return render(request, 'incident_form.html', context)

@login_required
def incident_delete(request, incident_id):
    incident = get_object_or_404(IncidentReport, pk=incident_id)
    
    if request.method == 'POST':
        incident.delete()
        messages.success(request, f'Incident report deleted successfully!')
        return redirect('incident_list')
    
    context = {'incident': incident, 'title': 'Delete Incident Report'}
    return render(request, 'incident_confirm_delete.html', context)

@login_required
def notification_list(request):
    try:
        user_profile = request.user.profile
        if user_profile and user_profile.user_type == 'ADMIN':
            notifications = Notification.objects.all().order_by('-created_at')
        else:
            elders = ElderProfile.objects.filter(guardian=request.user)
            notifications = Notification.objects.filter(
                Q(elder__in=elders) | Q(elder__isnull=True)
            ).order_by('-created_at')
    except UserProfile.DoesNotExist:
        elders = ElderProfile.objects.filter(guardian=request.user)
        notifications = Notification.objects.filter(
            Q(elder__in=elders) | Q(elder__isnull=True)
        ).order_by('-created_at')
    
    context = {'notifications': notifications}
    return render(request, 'notification_list.html', context)



@login_required
def notification_delete(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id)
    
    if request.method == 'POST':
        notification.delete()
        messages.success(request, 'Notification deleted successfully!')
        return redirect('notification_list')
    
    context = {'notification': notification, 'title': 'Delete Notification'}
    return render(request, 'notification_confirm_delete.html', context)

@login_required
def notification_mark_all_read(request):
    if request.method == 'POST':
        notifications = Notification.objects.filter(is_read=False)
        notifications.update(
            is_read=True,
            read_at=timezone.now(),
            read_by=request.user
        )
        messages.success(request, 'All notifications marked as read!')
    
    return redirect('notification_list')

@login_required
def notification_mark_read(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id)
    notification.is_read = True
    notification.read_at = timezone.now()
    notification.read_by = request.user
    notification.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    messages.success(request, 'Notification marked as read.')
    return redirect('notification_list')

@login_required
def user_profile(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = None
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            if profile:
                form.save()
            else:
                profile = form.save(commit=False)
                profile.user = request.user
                profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('user_profile')
    else:
        form = UserProfileForm(instance=profile)
    
    context = {'form': form, 'profile': profile}
    return render(request, 'user_profile.html', context)

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    context = {'form': form}
    return render(request, 'registration/register.html', context)

@login_required
def search(request):
    search_form = SearchForm(request.GET)
    query = request.GET.get('query', '')
    category = request.GET.get('category', 'all')
    results = {}
    
    if query:
        try:
            user_profile = request.user.profile
            if user_profile and user_profile.user_type == 'ADMIN':
                elders = ElderProfile.objects.all()
            else:
                elders = ElderProfile.objects.filter(guardian=request.user)
        except UserProfile.DoesNotExist:
            elders = ElderProfile.objects.filter(guardian=request.user)
        
        if category == 'elders' or category == 'all':
            results['elders'] = elders.filter(
                Q(full_name__icontains=query) |
                Q(medical_conditions__icontains=query) |
                Q(address__icontains=query)
            )
        
        if category == 'medications' or category == 'all':
            results['medications'] = MedicationSchedule.objects.filter(
                elder__in=elders
            ).filter(
                Q(medication__name__icontains=query) |
                Q(medication__description__icontains=query)
            )
        
        if category == 'tasks' or category == 'all':
            results['tasks'] = CareTask.objects.filter(
                elder__in=elders
            ).filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            )
        
        if category == 'appointments' or category == 'all':
            results['appointments'] = Appointment.objects.filter(
                elder__in=elders
            ).filter(
                Q(title__icontains=query) |
                Q(notes__icontains=query)
            )
    
    context = {
        'search_form': search_form,
        'query': query,
        'results': results,
    }
    return render(request, 'search_results.html', context)

def custom_logout(request):
    """Custom logout view that handles the logout process"""
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('login')
    else:
        # If accessed via GET, show logout confirmation
        return render(request, 'registration/logout_confirm.html')
