from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import Http404
from .models import UserProfile, ElderProfile

def admin_required(view_func):
    """Decorator to require admin access"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            user_profile = request.user.profile
            if user_profile and user_profile.user_type == 'ADMIN':
                return view_func(request, *args, **kwargs)
        except UserProfile.DoesNotExist:
            pass
        
        messages.error(request, "Administrator access required.")
        return redirect('dashboard')
    return _wrapped_view

def caregiver_required(view_func):
    """Decorator to require caregiver access"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            user_profile = request.user.profile
            if user_profile and user_profile.user_type in ['ADMIN', 'CAREGIVER', 'NURSE', 'DOCTOR']:
                return view_func(request, *args, **kwargs)
        except UserProfile.DoesNotExist:
            pass
        
        messages.error(request, "Caregiver access required.")
        return redirect('dashboard')
    return _wrapped_view

def medical_staff_required(view_func):
    """Decorator to require medical staff access (nurse/doctor)"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            user_profile = request.user.profile
            if user_profile and user_profile.user_type in ['ADMIN', 'NURSE', 'DOCTOR']:
                return view_func(request, *args, **kwargs)
        except UserProfile.DoesNotExist:
            pass
        
        messages.error(request, "Medical staff access required.")
        return redirect('dashboard')
    return _wrapped_view

def elder_access_required(view_func):
    """Decorator to require access to a specific elder"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        elder_id = kwargs.get('elder_id')
        if not elder_id:
            elder_id = kwargs.get('pk')
        
        if not elder_id:
            messages.error(request, "Elder ID required.")
            return redirect('elder_list')
        
        try:
            elder = ElderProfile.objects.get(pk=elder_id)
        except ElderProfile.DoesNotExist:
            raise Http404("Elder not found.")
        
        # Check if user has access to this elder
        try:
            user_profile = request.user.profile
            if user_profile and user_profile.user_type == 'ADMIN':
                # Admin can access all elders
                return view_func(request, *args, **kwargs)
            elif user_profile and user_profile.user_type in ['CAREGIVER', 'NURSE', 'DOCTOR']:
                # Medical staff can access elders they're assigned to
                if elder.guardian == request.user or elder in request.user.assigned_elders.all():
                    return view_func(request, *args, **kwargs)
            elif elder.guardian == request.user:
                # Guardian can access their own elders
                return view_func(request, *args, **kwargs)
        except UserProfile.DoesNotExist:
            if elder.guardian == request.user:
                return view_func(request, *args, **kwargs)
        
        messages.error(request, "You don't have permission to access this elder's information.")
        return redirect('elder_list')
    return _wrapped_view

def can_edit_elder(view_func):
    """Decorator to check if user can edit elder profile"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        elder_id = kwargs.get('elder_id')
        if not elder_id:
            elder_id = kwargs.get('pk')
        
        if not elder_id:
            messages.error(request, "Elder ID required.")
            return redirect('elder_list')
        
        try:
            elder = ElderProfile.objects.get(pk=elder_id)
        except ElderProfile.DoesNotExist:
            raise Http404("Elder not found.")
        
        # Check if user can edit this elder
        try:
            user_profile = request.user.profile
            if user_profile and user_profile.user_type == 'ADMIN':
                # Admin can edit all elders
                return view_func(request, *args, **kwargs)
            elif elder.guardian == request.user:
                # Guardian can edit their own elders
                return view_func(request, *args, **kwargs)
        except UserProfile.DoesNotExist:
            if elder.guardian == request.user:
                return view_func(request, *args, **kwargs)
        
        messages.error(request, "You don't have permission to edit this elder's profile.")
        return redirect('elder_detail', elder_id=elder.pk)
    return _wrapped_view
