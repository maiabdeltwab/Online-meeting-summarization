""" create your own template tags
    this file for user module tags
"""

from django import template

register = template.Library()

@register.filter(name='has_user')
def has_user(group, user_id):
    """ check if a user is a member to the group """
    userid = int(user_id)
    is_found = group.members.filter(pk=userid).first()
    return  is_found
