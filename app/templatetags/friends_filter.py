""" create your own template tags
    this file for user module tags
"""

from django import template

register = template.Library()

@register.filter(name='is_friends')
def is_friends(user1, user2):
    """ check if the two users are friends """
    is_found = user1.friends.filter(user2=user2).first()
    return  is_found

@register.filter(name='sent_freind_request')
def sent_request(user1, user2):
    """ check if user sent a friend request to profile owner """
    is_found = user1.request_from_user.filter(to_user=user2).first()
    return  is_found

@register.filter(name='receive_freind_request')
def receive_request(user1, user2):
    """ check if user received a friend request from profile owner """
    is_found = user1.request_to_user.filter(from_user=user2).first()
    return  is_found

@register.filter(name='mutual_friends')
def mutual_friends(friends, user):
    """ get mutual friends """
    count = 0
    for friend in friends:
        is_found = friend.user2.friends.filter(user2=user).first()
        if is_found:
            count += 1
    return count

@register.filter(name='mutual_groups')
def mutual_groups(groups, user):
    """ get mutual friends """
    count = 0
    for group in groups:
        is_found = group.members.filter(pk=user.id).first()
        if is_found:
            count += 1
    return count
    