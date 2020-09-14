"""
Database models
"""

from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# pylint: disable=invalid-name


class User_profile(models.Model):
    """ User profile model """
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='user_profile', primary_key=True)
    profile_pic = models.BinaryField()
    pic_path = models.ImageField(
        upload_to='upload/images', null=True, blank=True)
    gender = models.CharField(max_length=6, null=True, blank=True)
    birth_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.user.username} User_Profile'


class Group(models.Model):
    """ group table model """
    name = models.CharField(
        _('name'),
        max_length=150,
        help_text=_('Required. 150 characters or fewer'),
        null=False
    )
    description = models.CharField(
        _('group description'),
        max_length=500,
        null=True,
        blank=True
    )
    group_pic = models.BinaryField(null=True)
    pic_path = models.ImageField(
        upload_to='upload/images', null=True, blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE,
                                blank=True, null=True, related_name='group_creator')

    created_at = models.DateTimeField(default=timezone.now)
    call_start_at = models.DateTimeField(default=timezone.now)

    call_state = models.IntegerField(default=0)
    invite_code = models.CharField(null=True, max_length=500)
    members = models.ManyToManyField(User, related_name='group_members',
                                     through="group_members", blank=True)

    def __str__(self):
        return self.name


class group_members(models.Model):
    """ This model for many to many field between group and user to add additional fields """
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name='members_group')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='user_groups')
    in_call = models.IntegerField(default=0)


class Block_list(models.Model):
    """ block list model for users """
    from_user = models.ForeignKey(User, on_delete=models.CASCADE,
                                  related_name='block_from_user')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE,
                                related_name='block_to_user')

    class Meta:
        unique_together = ('from_user', 'to_user',)


class Block_groups_list(models.Model):
    """ block list model for groups """
    from_user = models.ForeignKey(User, on_delete=models.CASCADE,
                                  related_name='block_group')
    to_group = models.ForeignKey(Group, on_delete=models.CASCADE,
                                 related_name='block_to_group')

    class Meta:
        unique_together = ('from_user', 'to_group',)


class Friend_requests(models.Model):
    """ friend request list model """
    from_user = models.ForeignKey(User, on_delete=models.CASCADE,
                                  related_name='request_from_user')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE,
                                related_name='request_to_user')

    class Meta:
        unique_together = ('from_user', 'to_user',)


class Friends(models.Model):
    """ Friend list for users  """
    user1 = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='friends')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='user2')

    class Meta:
        unique_together = ('user1', 'user2',)


class Audio_group_call(models.Model):
    """ To store audio group meetings record and its nlp files/paths """
    group = models.ForeignKey(Group, on_delete=models.CASCADE,
                              related_name='call_from_group')
    title = models.CharField(
        _('title'),
        max_length=300,
        help_text=_('Required. 150 characters or fewer'),
        null=True
    )
    state = models.IntegerField(null=True, default=0)
    audio_file = models.BinaryField(null=False)
    audio_file_path = models.FileField(upload_to='upload/audiofiles', blank=True,
                                       validators=[FileExtensionValidator(
                                           allowed_extensions=['wav'])],
                                       help_text=("Allowed type - .wav"))
    stt_file = models.BinaryField(null=True)  # speech to text file
    stt_file_path = models.FileField(
        upload_to='upload/punctuated_text', null=True, blank=True)
    summarization_file = models.BinaryField(null=True)
    sum_file_path = models.FileField(
        upload_to='upload/text_summarization', null=True, blank=True)
    call_date = models.DateTimeField(default=timezone.now)


class Audio_private_call(models.Model):
    """ To store audio private record and its nlp files/paths """
    user1 = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='calling_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='calling_user2')
    title = models.CharField(
        _('title'),
        max_length=300,
        help_text=_('Required. 150 characters or fewer'),
        null=True
    )
    state = models.IntegerField(null=True)
    audio_file = models.BinaryField(null=False)
    audio_file_path = models.FileField(upload_to='upload/audiofiles', blank=True,
                                       validators=[FileExtensionValidator(
                                           allowed_extensions=['wav'])],
                                       help_text=("Allowed type - .wav"))
    stt_file = models.BinaryField(null=True)  # speech to text file
    stt_file_path = models.FileField(
        upload_to='upload/punctuated_text', null=True, blank=True)
    summarization_file = models.BinaryField(null=True)
    sum_file_path = models.FileField(
        upload_to='upload/text_summarization', null=True, blank=True)
    call_date = models.DateTimeField(default=timezone.now)


class Group_messages(models.Model):
    """ Model for messages for each group """
    group = models.ForeignKey(Group, on_delete=models.CASCADE,
                              related_name='message_from_group')
    sender = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='user_member_sender')
    message_date = models.DateTimeField(default=timezone.now)
    content_text = models.CharField(max_length=1000, null=True)
    attached_file = models.BinaryField(null=True)

    class Meta:
        ordering = ('message_date', )


class Private_messages(models.Model):
    """ Model for private messages """
    sender = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='user_sender')
    chat = models.ForeignKey(Friends, on_delete=models.CASCADE,
                             related_name='private_chat_id', null=True)
    message_date = models.DateTimeField(default=timezone.now)
    content_text = models.CharField(max_length=1000, null=True)
    attached_file = models.BinaryField(null=True)

    class Meta:
        ordering = ('message_date', )


class DataBase_search(models.Model):
    """ this model to store database search """
    search_text = models.CharField(max_length=1000, null=True)
       
