"""  admin tables """
import os

from django.contrib import admin
import app.models as models

admin.site.register(models.User_profile)
admin.site.register(models.Audio_group_call)
admin.site.register(models.Audio_private_call)
admin.site.register(models.Block_groups_list)
admin.site.register(models.Block_list)
admin.site.register(models.Friend_requests)
admin.site.register(models.Friends)
admin.site.register(models.Group)
admin.site.register(models.Group_messages)
admin.site.register(models.Private_messages)

