from django.urls import path
from . import views

urlpatterns = [
    # Dashboard and main views
    path('', views.dashboard, name='dashboard'),
    path('search/', views.search, name='search'),
    
    # Elder management
    path('elders/', views.elder_list, name='elder_list'),
    path('elders/add/', views.elder_add, name='elder_add'),
    path('elders/<int:elder_id>/', views.elder_detail, name='elder_detail'),
    path('elders/<int:elder_id>/edit/', views.elder_edit, name='elder_edit'),
    
    # Medication management
    path('medications/', views.medication_list, name='medication_list'),
    path('medications/add/', views.medication_add, name='medication_add'),
    path('medications/<int:medication_id>/edit/', views.medication_edit, name='medication_edit'),
    path('medications/<int:medication_id>/delete/', views.medication_delete, name='medication_delete'),
    path('medications/schedule/add/', views.med_schedule_add, name='med_schedule_add'),
    path('medications/schedule/<int:schedule_id>/log/', views.medication_log, name='medication_log'),
    path('medications/log/add/', views.medication_log_add, name='medication_log_add'),
    path('elders/<int:elder_id>/medications/', views.medication_list, name='elder_medications'),
    
    # Appointment management
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/add/', views.appointment_add, name='appointment_add'),
    path('appointments/<int:appointment_id>/edit/', views.appointment_edit, name='appointment_edit'),
    path('appointments/<int:appointment_id>/delete/', views.appointment_delete, name='appointment_delete'),
    path('elders/<int:elder_id>/appointments/', views.appointment_list, name='elder_appointments'),
    
    # Care task management
    path('tasks/', views.care_task_list, name='care_task_list'),
    path('tasks/add/', views.care_task_add, name='care_task_add'),
    path('tasks/<int:task_id>/edit/', views.care_task_edit, name='care_task_edit'),
    path('tasks/<int:task_id>/complete/', views.care_task_complete, name='care_task_complete'),
    path('tasks/<int:task_id>/delete/', views.care_task_delete, name='care_task_delete'),
    path('elders/<int:elder_id>/tasks/', views.care_task_list, name='elder_tasks'),
    
    # Emergency contacts
    path('elders/<int:elder_id>/emergency-contacts/', views.emergency_contacts, name='emergency_contacts'),
    path('elders/<int:elder_id>/emergency-contacts/add/', views.emergency_contact_add, name='emergency_contact_add'),
    path('emergency-contacts/<int:contact_id>/edit/', views.emergency_contact_edit, name='emergency_contact_edit'),
    path('emergency-contacts/<int:contact_id>/delete/', views.emergency_contact_delete, name='emergency_contact_delete'),
    
    # Vitals tracking
    path('vitals/', views.vitals_list, name='vitals_list'),
    path('vitals/add/', views.vitals_add, name='vitals_add'),
    path('vitals/<int:vital_id>/', views.vitals_detail, name='vitals_detail'),
    path('vitals/<int:vital_id>/edit/', views.vitals_edit, name='vitals_edit'),
    path('vitals/<int:vital_id>/delete/', views.vitals_delete, name='vitals_delete'),
    path('elders/<int:elder_id>/vitals/', views.vitals_list, name='elder_vitals'),
    path('elders/<int:elder_id>/vitals/add/', views.vitals_add, name='elder_vitals_add'),
    path('elders/<int:elder_id>/vitals/quick/', views.quick_vitals, name='quick_vitals'),
    
    # Incident reporting
    path('incidents/', views.incident_list, name='incident_list'),
    path('incidents/add/', views.incident_add, name='incident_add'),
    path('incidents/<int:incident_id>/edit/', views.incident_edit, name='incident_edit'),
    path('incidents/<int:incident_id>/delete/', views.incident_delete, name='incident_delete'),
    path('elders/<int:elder_id>/incidents/', views.incident_list, name='elder_incidents'),
    
    # Notifications
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:notification_id>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/<int:notification_id>/delete/', views.notification_delete, name='notification_delete'),
    path('notifications/mark-all-read/', views.notification_mark_all_read, name='notification_mark_all_read'),
    
    # User management
    path('profile/', views.user_profile, name='user_profile'),
    path('register/', views.register, name='register'),
]
