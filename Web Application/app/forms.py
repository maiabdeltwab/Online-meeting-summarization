"""
Definition of forms.
"""
import os

import django.contrib.auth.forms as auth_forms
from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from notifications.models import Notification
from notifications.signals import notify

import app.models as models
import NLP.Punctuation.Punctuator as punc
import NLP.speech_to_text.silence_segmentation as stt_voice
import NLP.SpeechToText as stt
#import NLP.TextSummarization.Abstract as ts
import NLP.TextSummarization.BertExtractive as ts
from MeetApp.settings import MEDIA_ROOT

# pylint: disable=trailing-whitespace
# pylint: disable=pointless-string-statement
# pylint: disable=bare-except

''''''
''' ===========================> User forms <=========================== '''
''''''


class AuthenticationForm(auth_forms.AuthenticationForm):
    """Authentication form which uses boostrap CSS."""
    username = forms.CharField(max_length=254,
                               widget=forms.TextInput({
                                   'class': 'form-control',
                                   'placeholder': 'username'}))
                                   #form-control form-control-danger
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput({
                                   'class': 'form-control',
                                   'placeholder': 'Password'}))


class UserCreationForm(auth_forms.UserCreationForm):
    """UserCreationForm form which uses boostrap CSS."""
    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
        widget=forms.PasswordInput({
            'class': 'form-control form-control-user',
            'id' : 'password1',
            'placeholder': 'Password'}),)
    password2 = forms.CharField(
        label=_("Password confirmation"),
        strip=False,
        help_text=_("Enter the same password as before, for verification."),
        widget=forms.PasswordInput({
            'class': 'form-control form-control-user',
            'id' : 'password1',
            'placeholder': 'Repeat password'}),)
    username = forms.CharField(max_length=254,
                               widget=forms.TextInput({
                                   'class': 'form-control form-control-user',
                                   'id' : 'username',
                                   'placeholder': 'Username'}))

    first_name = forms.CharField(max_length=30, required=True, help_text='Optional.',
                                 widget=forms.TextInput({
                                     'class': 'form-control form-control-user',
                                     'id' : 'first_name',
                                     'placeholder': 'first name'}))
    last_name = forms.CharField(max_length=30, required=True, help_text='Optional.',
                                widget=forms.TextInput({
                                    'class': 'form-control form-control-user',
                                    'id' : 'last_name',
                                    'placeholder': 'last name'}))
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.',
                             widget=forms.TextInput({
                                 'class': 'form-control form-control-user',
                                 'id' : 'email',
                                 'placeholder': 'email'}))
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name',
                  'email', 'password1', 'password2', )
                  

    def create_profile(self, user_instance):
        """ this method take user and create a user_profile object for this user """
        try:
            # create profile with same user id
            models.User_profile.objects.create(user=user_instance)
            print("profile has been created successfully")
        except:
            print("An exception occurred in create_profile")


class UserChangeForm(forms.ModelForm):
    """UserChangeForm form which uses boostrap CSS."""
    username = forms.CharField(max_length=254,
                               widget=forms.TextInput({
                                   'class': 'form-control form-control-user',
                                   'placeholder': 'Username'}))

    first_name = forms.CharField(max_length=30, required=True, help_text='Optional.',
                                 widget=forms.TextInput({
                                     'class': 'form-control form-control-user',
                                     'placeholder': 'first name'}))
    last_name = forms.CharField(max_length=30, required=True, help_text='Optional.',
                                widget=forms.TextInput({
                                    'class': 'form-control form-control-user',
                                    'placeholder': 'last name'}))
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.',
                             widget=forms.TextInput({
                                 'class': 'form-control form-control-user',
                                 'placeholder': 'email'}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email',)


class UserProfileChangeForm(forms.ModelForm):
    """ profile form """
    pic_path = forms.ImageField(required=True, label=_("change photo"),
                                widget=forms.FileInput({
                                    'class': 'custom-file-input text-info',
                                    'placeholder': 'file path'}))

    class Meta:
        model = models.User_profile
        fields = ('pic_path',)

    def change_user_photo(self, user_id, path):
        """ this method take user id and the path where image had been uploaded
            ==> read image from path then save it in database """
        try:
            # read the upload image file from the given path
            with open(path, 'rb') as file:
                imagefile = file.read()

            # get the model by given id, update it to save the image file
            models.User_profile.objects.filter(
                pk=user_id).update(profile_pic=imagefile)

            # os.remove(path) #remove the image from path after save it
            print("1 row updateded successfully")
        except:
            print("An exception occurred in change_user_photo")

    def remove_photo(self, username):
        """ this method to remove user picture """
        user = User.objects.filter(username=username).first()
        models.User_profile.objects.filter(pk=user.id).update(
            profile_pic=None, pic_path=None)

    def remove_group(self, user, group_id):
        """ this method to remove user from group """
        user.group_members.remove(group_id)

    def add_friend(self, from_user, to_user):
        """ this method to send friend request """
        request = models.Friend_requests(from_user=from_user, to_user=to_user)
        request.save()

        #create a notification object to inform the user
        notify.send(to_user, recipient=to_user, verb='friend_req', target=from_user)

    def cancel_request(self, from_user, to_user):
        """ this method to cancel friend request (sender) """
        #delete request
        request = models.Friend_requests.objects.filter(
            from_user=from_user, to_user=to_user).first()

        #delete notification
        # note = Notification.objects.filter(
        #     verb="friend_req", recipient=to_user, target=from_user).first()
        # note.delete()
        request.delete()

    def delete_request(self, to_user, from_user):
        """ this method to delete friend request (receiver) """
        request = models.Friend_requests.objects.filter(
            from_user=from_user, to_user=to_user).first()
        #delete notification
        # note = Notification.objects.filter(
        #     verb="friend_req", recipient=to_user, target=from_user).first()
        # note.delete()
        request.delete()

    def confirm_request(self, to_user, from_user):
        """ this method to accept friend request """
        self.delete_request(to_user, from_user)  # delete request
        # add them to friends table
        friend1 = models.Friends(user1=to_user, user2=from_user)
        friend1.save()
        friend2 = models.Friends(user2=to_user, user1=from_user)
        friend2.save()

        # send notification to the second user (user1 accept user request)
        notify.send(from_user, recipient=from_user, verb='accept_req', target=to_user)

    def delete_friend(self, user1, user2):
        """ this method to delete friend """
        friend1 = models.Friends.objects.filter(
            user1=user1, user2=user2).first()
        friend1.delete()
        friend2 = models.Friends.objects.filter(
            user2=user1, user1=user2).first()
        friend2.delete()

    def block_user(self, from_user, to_user):
        """ this method to block user """
        try:
            self.cancel_request(from_user, to_user)
        except:
            print('escape')
        try:
            self.delete_friend(from_user, to_user)
        except:
            print('escape')
        try:
            self.delete_request(to_user, from_user)
        except:
            print('escape')
        block = models.Block_list(from_user=from_user, to_user=to_user)
        block.save()

    def unblock_user(self, user, blocked_userid):
        """ this method to unblock user """
        blocked_user = User.objects.filter(pk=blocked_userid).first()
        blocked = models.Block_list.objects.filter(
            from_user=user, to_user=blocked_user).first()
        blocked.delete()

    def delete_account(self, user):
        """ this method to delete user account """
        user.delete()


class PasswordChangeForm(auth_forms.PasswordChangeForm):
    """UserCreationForm form which uses boostrap CSS."""
    old_password = forms.CharField(
        label=_("Password"),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
        widget=forms.PasswordInput({
            'class': 'form-control form-control-user',
            'placeholder': 'Old Password'}),)

    new_password1 = forms.CharField(
        label=_("Password confirmation"),
        strip=False,
        widget=forms.PasswordInput({
            'class': 'form-control form-control-user',
            'placeholder': 'Enter new password'}),)

    new_password2 = forms.CharField(
        label=_("Password confirmation"),
        strip=False,
        widget=forms.PasswordInput({
            'class': 'form-control form-control-user',
            'placeholder': 'Repeat new password'}),)

    class Meta:
        model = User
        fields = ('old_password', 'new_password1', 'new_password2')


class PasswordResetForm(auth_forms.PasswordResetForm):
    """PasswordResetForm form which uses boostrap CSS."""
    email = forms.EmailField(label=_("Email"), max_length=254,
                             widget=forms.TextInput({
                                 'class': 'form-control form-control-user',
                                 'placeholder': 'E-mail'}))


class SetPasswordForm(auth_forms.SetPasswordForm):
    """
    A form that lets a user change set their password without entering the old
    password
    """
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
        'password_notvalid': _("Password must of 8 Character which contain"
                               + "alphanumeric with atleast 1 special charater and 1 uppercase."),
    }
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput({'class': 'form-control form-control-user',
                                    'placeholder': 'New password'}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=forms.PasswordInput({'class': 'form-control form-control-user',
                                    'placeholder': 'New password confirmation'}),
    )


''''''
''' ===========================> group forms <=========================== '''
''''''


class CreateGroup(forms.ModelForm):
    """ create new group form """
    name = forms.CharField(max_length=150, required=False, label=_("Group Name"),
                           widget=forms.TextInput({
                               'class': 'form-control form-control-user',
                               'placeholder': 'Groub Name'}))
    description = forms.CharField(max_length=500, required=False, label=_("Description"),
                                  widget=forms.TextInput({
                                      'class': 'form-control form-control-user',
                                      'placeholder': 'Group description (optional)'}))

    class Meta:
        model = models.Group
        fields = ('name', 'description',)

    def save_user(self, group, user):
        """ this method take group id and get the user from view
            ==> save user to group creator """
        try:

            # get the model by given id, update it to save the image file
            models.Group.objects.filter(pk=group.id).update(creator=user)
            group.members.add(user)
            print("user have been updated successfully")

        except:
            print("An exception occurred in save_user")


class UpdateGroupImage(forms.ModelForm):
    """  update group picture form """
    pic_path = forms.ImageField(required=True, label=_("group image"),
                                widget=forms.FileInput({
                                    'class': 'custom-file-input',
                                    'placeholder': 'file path'}))

    class Meta:
        model = models.Group
        fields = ('pic_path',)

    def save_group_pic(self, group_id, path):
        """ this method take group id and the path where image had been uploaded
            ==> read image from path then save it in database """
        try:

            # read the upload image file from the given path
            with open(path, 'rb') as file:
                imagefile = file.read()

            # get the model by given id, update it to save the image file
            models.Group.objects.filter(
                pk=group_id).update(group_pic=imagefile)

            # os.remove(path) #remove the image from path after save it
            print("1 row updateded successfully")

        except:
            print("An exception occurred in save_group_pic")

    def remove_photo(self, groupid):
        """ this method to remove group picture """
        models.Group.objects.filter(pk=groupid).update(
            group_pic=None, pic_path=None)

    def remove_group(self, groupid):
        """ this method to remove group """
        models.Group.objects.filter(pk=groupid).delete()


class AddGroupMembers(forms.ModelForm):
    """ add members to given group form """
    search_text = forms.CharField(max_length=150, required=False, label=_("Group Name"),
                                  widget=forms.TextInput({
                                      'class': 'form-control m-t-15',
                                      'placeholder': 'Search for username...'}))
    class Meta:
        model = models.DataBase_search
        fields = ('search_text',)

    def add_user(self, group, user_id):
        """ this method to add user to group """
        group.members.add(user_id)

        # send notification to the this user
        user = User.objects.filter(pk=user_id).first()
        notify.send(user, recipient=user, verb='add_group', target=group)

    def remove_user(self, group, user_id):
        """ this method remove the user from group """
        group.members.remove(user_id)


''''''
''' ========================> audio group forms <======================== '''
''''''


class UploadGroupAudio(forms.ModelForm):
    """ Upload previously recorded meeting form """
    title = forms.CharField(max_length=150, required=False, label=_("meeting  title"),
                            widget=forms.TextInput({
                                'class': 'form-control form-control-user',
                                'placeholder': 'title (optional).'}))

    audio_file_path = forms.FileField(required=True, widget=forms.FileInput({
        'class': 'custom-file-input',
        'placeholder': 'file path',
        'name': 'file',
        'accept': ".wav"}))

    class Meta:
        model = models.Audio_group_call
        fields = ('title', 'audio_file_path')

    def save_group_audio(self, audio_id, path):
        """ this method take audio id and the path where file had been uploaded
            ==> read audio from path then save it in database """
        try:

            path = os.path.join(MEDIA_ROOT, path)
            # read the upload audio file from the given path
            with open(path, 'rb') as file:
                audiofile = file.read()

            # get the model by given id, update it to save the audio file
            models.Audio_group_call.objects.filter(
                pk=audio_id).update(audio_file=audiofile)

            # os.remove(path) #remove the file from path after save it
            print("1 row updateded successfully")

        except:
            print("An exception occurred in save_group_audio")

    # first spech to text (not used)
    def speech_to_text(self, audio_id, audiofilepath):
        """ this method take audio id and the path where file had been uploaded
            ==> apply speech recognition and punctuation algorithms on audio 
            ==> save the output as txt file into database """

        stt_file_path = stt.speech_to_text(
            audiofilepath)  # apply speech to text
        punctuated_text_path = punc.punctuator(
            stt_file_path)  # apply punctuation

        # read the output file from the returned path
        path = os.path.join(MEDIA_ROOT, punctuated_text_path)
        with open(path, 'rb') as file:
            stt_file = file.read()

        # get the model by given id, update it to save the stt file
        models.Audio_group_call.objects.filter(
            pk=audio_id).update(stt_file=stt_file, state=2)

        # delete the uploaded audio file from its path
        # os.remove(audiofilepath)

        return punctuated_text_path

    def text_summarization(self, audio_id, stt_path):
        """ this method take audio id and the stt output file path
          ==> apply text summarization algorithm on stt output
          ==> save the output as txt file into database """
        stt_path = os.path.join(MEDIA_ROOT, stt_path)
        ts_file_path = ts.text_summarization(stt_path)  # apply speech to text

        # read the output file from the returned path
        path = os.path.join(MEDIA_ROOT, ts_file_path)
        with open(path, 'rb') as file:
            summary_file = file.read()

        # get the model by given id, update it to save the stt file
        models.Audio_group_call.objects.filter(pk=audio_id).update(
            summarization_file=summary_file)

        # delete the stt and ts files from their path
        # os.remove(stt_path)
        # os.remove(ts_file_path)

        return ts_file_path

    def stt_voice_recog(self, audio_id, audiofilepath):
        """ this method take audio id and the path where file had been uploaded
            ==> apply speech recognition and punctuation algorithms on audio 
            ==> save the output as txt file into database """

        stt_only, stt_with_speakers = stt_voice.speech_to_text(
            audiofilepath)  # apply speech to text with voice recognition

        # read the output file from the returned path
        path = os.path.join(MEDIA_ROOT, stt_with_speakers)
        with open(path, 'rb') as file:
            stt_file = file.read()

        # get the model by given id, update it to save the stt file
        models.Audio_group_call.objects.filter(
            pk=audio_id).update(stt_file=stt_file)

        # delete the uploaded audio file from its path
        # os.remove(audiofilepath)

        return stt_only, stt_with_speakers


''''''
''' ========================> notifications <======================== '''
''''''


def make_notice_read(noticeid):
    """ thke notification id
        => and make this notification read """
    notice = Notification.objects.filter(pk=noticeid)
    notice.mark_all_as_read()
