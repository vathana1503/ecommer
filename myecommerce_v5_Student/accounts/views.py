from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm, UserProfileForm, UserUpdateForm
from .models import UserProfile
from .decorators import staff_or_owner_required


def register_view(request):
    """
    User registration view with automatic profile creation
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            # Auto-login the user after registration
            login(request, user)
            return redirect('accounts:profile')
    else:
        form = CustomUserCreationForm()
    
    context = {
        'form': form,
        'title': 'Register'
    }
    return render(request, 'accounts/register.html', context)


def login_view(request):
    """
    User login view with role-based redirection
    """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f'Welcome back, {username}!')
                
                # Redirect based on user role
                if hasattr(user, 'profile'):
                    if user.profile.can_access_dashboard():
                        return redirect('store:dashboard')
                    else:
                        return redirect('store:home')
                else:
                    return redirect('accounts:profile')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    context = {
        'form': form,
        'title': 'Login'
    }
    return render(request, 'accounts/login.html', context)


def logout_view(request):
    """
    User logout view
    """
    logout(request)
    messages.info(request, 'You have successfully logged out.')
    return redirect('store:home')


@login_required
def profile_view(request):
    """
    User profile view - display user information
    """
    # Ensure user has a profile (backup in case signal failed)
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    context = {
        'user': request.user,
        'profile': profile,
        'title': 'My Profile'
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile_view(request):
    """
    Edit user profile view
    """
    # Ensure user has a profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile, user=request.user)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'title': 'Edit Profile'
    }
    return render(request, 'accounts/edit_profile.html', context)
