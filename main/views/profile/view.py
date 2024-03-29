"""
Profile views
"""
import logging
from enum import Enum
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetView
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from main.forms.profile.forms import NewUserForm, ResetPasswordForm
from main.utils.database_utils import get_user_reviews
from rental_app.settings import EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
import common

logger = logging.getLogger()

class Forgot(Enum):
    PASSWORD = 1
    USERNAME = 2

def forgot_username(request) -> HttpResponse:
    """
    /forgot-username
    Forgot username workflow
    Returns the user to the login page
    """
    if request.method == "POST":
        _send_forgot_email(request, Forgot.USERNAME)
        return render(
            request, common.FORGOT_USERNAME_FORM_TEMPLATE, {
                "message": "If there is a user with that email address, you'll receive an email shortly"
            }
        )
    return render(request, common.FORGOT_USERNAME_FORM_TEMPLATE)


def password_reset(request) -> HttpResponse:
    """
    /password-reset
    """
    if request.method == "POST":
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                subject_template_name=common.PASSWORD_RESET_EMAIL_SUBJECT_FILE,
                email_template_name=common.PASSWORD_RESET_EMAIL_FORM_TEMPLATE,
                html_email_template_name=common.PASSWORD_RESET_EMAIL_FORM_TEMPLATE,
                extra_email_context=None,
            )
            return redirect("user_login")
    else:
        form = ResetPasswordForm()
    return render(request, common.FORGOT_PASSWORD_FORM_TEMPLATE, {"form": form})


def _send_forgot_email(request, forgot: Forgot):
    email = request.POST.get("email")
    try:
        user = User.objects.get(email=email)
        domain = HttpRequest.get_host(request)
        protocol = "https" if request.is_secure() else "http"
        if forgot == Forgot.USERNAME:
            _send_username_email(email, user, domain, protocol)
    except User.DoesNotExist:
        pass


def _send_username_email(email, user, domain, protocol):
    email_html = render_to_string(
        common.FORGOT_USERNAME_EMAIL,
        {"username": user.username, "domain": domain, "protocol": protocol},
    )
    send_mail(
        "Rentalranter Username",
        "",
        EMAIL_HOST_USER,
        [email],
        fail_silently=False,
        auth_user=EMAIL_HOST_USER,
        auth_password=EMAIL_HOST_PASSWORD,
        html_message=email_html,
    )


def register(request) -> HttpResponse:
    """
    /register
    Register a new user
    Forwards the user to the registration page
    """
    logger.info(request.META)
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # If registering, go back from whence you came
            if 'relay_state_url' in request.session:
                redirect_url = request.session['relay_state_url']
                request.session.pop('relay_state_url', None)
                return redirect(redirect_url)
            request.session[common.USERNAME] = user.get_username
            return user_profile(request)

        logger.warning("Could not register user. %s", form.errors.as_json)
        return render(
            request,
            template_name=common.NEW_USER_FORM_TEMPLATE,
            context={"errors": form.errors, "register_form": form},
        )
    form = NewUserForm()
    return render(
        request,
        template_name=common.NEW_USER_FORM_TEMPLATE,
        context={"register_form": form},
    )


@login_required
def user_profile(request) -> HttpResponse:
    """
    /profile
    Render user profile template
    """
    username = request.user.username
    if request.user.is_authenticated and request.user.is_staff:
        return redirect(reverse('admin:index'))
    
    user_reviews = get_user_reviews(username)
    return render(
        request,
        template_name=common.USER_PROFILE_TEMPLATE,
        context={"username": username, "user_reviews": user_reviews}
    )


def user_login(request) -> HttpResponse:
    """
    /login
    Show the user login template.
    Log the user in and redirect to the user profile page
    """
    if request.method == "POST":
        forgot_username(request)

        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                if 'relay_state_url' in request.session:
                    return redirect(request.session["relay_state_url"])
                redirect_url = reverse("user_profile")
                return redirect(redirect_url)
            else:
                return render(
                    request,
                    template_name=common.LOGIN_FORM_TEMPLATE,
                    context={"login_form": form, "errors": form.errors},
                )
        else:
            return render(
                request,
                template_name=common.LOGIN_FORM_TEMPLATE,
                context={"login_form": form, "errors": form.errors},
            )
    elif request.user.username:
        redirect_url = reverse("user_profile")
        return redirect(redirect_url)
    form = AuthenticationForm()
    return render(
        request=request,
        template_name=common.LOGIN_FORM_TEMPLATE,
        context={"login_form": form},
    )


def user_logout(request) -> HttpResponseRedirect:
    """
    /logout
    Log the user out and redirect back to home page
    """
    logout(request)
    return redirect("/")


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = common.PASSWORD_RESET_CONFIRM_FORM_TEMPLATE
    success_url = reverse_lazy("user_login")
