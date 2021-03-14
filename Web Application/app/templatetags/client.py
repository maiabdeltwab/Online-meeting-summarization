""" create your own template tages  (this file not used) """

from django import template
from django.utils import timezone
import voice_call.client as client

register = template.Library()

@register.simple_tag
def create_client(group, server_ip, group_member):
    """ create client useing simple tage """
    user_client = client.Client(server_ip, group.call_state, group_member)
    return  user_client


@register.filter(name='in_call')
def in_call(user, group):
    """ check if user in group call """
    is_found = user.user_groups.filter(group=group).first().in_call
    return  is_found

@register.simple_tag
def call_time(group):
    """ return the call time """
    time = (timezone.now()-group.call_start_at).total_seconds()
    time = int(time)
    return  time
