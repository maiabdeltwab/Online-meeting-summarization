''' Django notifications template tags file '''
# -*- coding: utf-8 -*-
from django.template import Library

from notifications.models import Notification

register = Library()


@register.simple_tag
def notify_list(user):
    """ return list of all notification for this user """
    notices = Notification.objects.filter(recipient=user)
    return notices


