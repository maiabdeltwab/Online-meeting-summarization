"""
Definition of urls for MeetApp.
"""

from datetime import datetime

import notifications.urls
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import include, path
from django.views.generic import TemplateView

from app import forms, views
from MeetApp import settings

urlpatterns = [
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    url('', include('social_django.urls', namespace='social')),
    url('^inbox/notifications/', include(notifications.urls, namespace='notifications')),
    # login
    path('login/',
         LoginView.as_view
         (
             template_name='app/user/login.html',
             authentication_form=forms.AuthenticationForm,
             extra_context={
                 'title': 'Log in',
                 'year': datetime.now().year,
             }
         ),
         name='login'),

    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),

    path('admin/', admin.site.urls),

    # signup
    path('signup/', views.signup, name='signup'),

    # Forget Password
    path('password_reset/',
         auth_views.PasswordResetView.as_view(
             form_class=forms.PasswordResetForm,
             template_name='app/user/forgot-password.html',
             subject_template_name='app/user/password_reset_subject.txt',
             html_email_template_name='app/user/forgot-password-email.html',
             extra_context={
                 'title': 'Reset password',
                 'year': datetime.now().year,
             }
         ),
         name='password_reset_form'),

    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='app/user/forgot-password-check-mail.html',
             extra_context={
                 'title': 'reset password done',
                 'year': datetime.now().year,
             }
         ),
         name='password_reset_done'),

    path('password-reset/confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='app/user/forgot-password-reset.html',
             form_class=forms.SetPasswordForm,
             extra_context={
                 'title': 'reset password confirm',
                 'year': datetime.now().year,
             }
         ),
         name='password_reset_confirm'),

    path('password_reset_complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='app/user/forgot-password-complete.html',
             extra_context={
                 'title': 'reset password complete',
                 'year': datetime.now().year,
             }
         ),
         name='password_reset_complete'),

    path('AccountSettings/', views.AccountSettings, name='accountsettings'),
    path('AccountSettings/<userid>', views.AccountSettings, name='accountsettings'),

    path('profile/<username>/', views.profile, name='profile'),
    path('profile/<username>/<noticeid>/<groupid>', views.profile, name='profile'),

    path('creategroup/', views.CreateGroup, name='creategroup'),
    path('addGroupMembers/<groupid>/',
         views.AddGroupMembers, name='addGroupMembers'),
    path('addGroupMember/<groupid>/<userid>/',
         views.AddGroupMembers, name='addGroupMember'),

    path('viewgroup/<groupid>/', views.ViewGroup, name='viewGroup'),
    path('viewgroup/<groupid>/<noticeid>', views.ViewGroup, name='viewGroup'),
    path('viewgroup/<groupid>/<userid>/',
         views.ViewGroup, name='viewGroupMember'),

    path('groupcall/<groupid>/', views.GroupCall, name='groupCall'),

    path('upload/group/audio/<groupid>/',
         views.UploadGroupAudio, name='upload_group_audio'),

    path('group/meetings/', views.GroupAudios, name='group_meetings'),
    path('groups/meetings/<noticeid>', views.GroupAudios, name='group_meetings'),
    path('group/meetings/refresh/', views.refresh_audio_table,
         name='refresh_group_meetings'),

    path('group/meeting/<audio_id>/', views.GroupAudio, name='group_meeting'),
    path('group/meeting/<audio_id>/<noticeid>', views.GroupAudio, name='group_meeting'),

    url(r'^logout/$', auth_views.auth_logout,
        {'next_page': settings.LOGOUT_REDIRECT_URL}, name='logout'),

    path('notifications/', TemplateView.as_view(template_name="app/notifications.html",
                                                extra_context={'title': 'notifications center',
                                                               'year': datetime.now().year,
                                                              }), name='notifications'),

    path('notfound/', TemplateView.as_view(template_name="app/not_found.html",
                                           extra_context={'title': 'page not found',
                                                          'year': datetime.now().year,
                                                         }), name='notFound'),]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
