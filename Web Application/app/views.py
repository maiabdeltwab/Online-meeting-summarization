"""
Definition of views.
"""
from datetime import datetime

import basehash
from django.contrib.auth import (authenticate, get_user, login,
                                 update_session_auth_hash)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

import app.forms as forms
import app.models as models
import app.tasks as tasks
import voice_call.client as Client
import voice_call.server as Server

# pylint: disable=pointless-string-statement
# pylint: disable=trailing-whitespace
# pylint: disable=invalid-name 

''''''
''' ===========================> Main views <=========================== '''
''''''


def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/index.html',
        {
            'title': 'Home Page',
            'year': datetime.now().year,
        }
    )


def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/contact.html',
        {
            'title': 'Contact',
            'message': 'Your contact page.',
            'year': datetime.now().year,
        }
    )


def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/about.html',
        {
            'title': 'About',
            'message': 'Your application description page.',
            'year': datetime.now().year,
        }
    )


''''''
''' ===========================> User views <=========================== '''
''''''


def signup(request):

    """Renders the Registration page"""

    if request.method == 'POST': 

        form = forms.UserCreationForm(request.POST) #create this form to take user input

        if form.is_valid(): #check the validation of this data

            user_instance = form.save() #save user in db
            form.create_profile(user_instance)  # create profile object for this user

            #take input username and password from template to log user in
            username = form.cleaned_data.get('username') 
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password) #authenticate this user
            login(request, user) #then login

            return redirect('home') #send user to home page

    else:
        form = forms.UserCreationForm() #for get request send empty form

    #render page and send contexts
    assert isinstance(request, HttpRequest)
    return render(request, 'app/user/register.html',
                  {
                      'title': 'Signup',
                      'year': datetime.now().year,
                      'form': form,
                  })


@login_required(login_url='login')
def AccountSettings(request, userid=None):
    """Renders the profile settings page"""
    user = get_user(request) #get user obj from session

    ''' define forms '''
    user_form = forms.UserChangeForm(instance=user) # this form to update user info.
    password_form = forms.PasswordChangeForm(
        user=request.user)  # this form to change user password
    profile_form = forms.UserProfileChangeForm() #and this to change/remove and set user picture

    block_list = models.Block_list.objects.filter(from_user=user) #get user blocked list
   
    if request.method == 'POST': 
        # save settings request 
        if request.POST.get("user_info") == 'true':
            user_form = forms.UserChangeForm(request.POST, instance=user) #get input data
            if user_form.is_valid():
                user_form.save() #save settings
                return redirect('accountsettings') #redirect to same page

        #update password request 
        elif request.POST.get("user_pass") == 'true':
            password_form = forms.PasswordChangeForm(
                user=request.user, data=request.POST) #get data
            if password_form.is_valid():
                user = password_form.save()
                # to keep user logged in after change password
                update_session_auth_hash(request, user)
                #to home page (can't redirect to the same page till complete auth process)
                return redirect('/') 

        #unblock user request
        elif request.POST.get("unblock_user") == 'true':
            profile_form.unblock_user(user, userid)  

        #delete account request (permanently deletion)
        elif request.POST.get("delete_account") == 'true':
            profile_form.delete_account(user)
            return redirect('login') #send to login page

    
    context = {'block_list': block_list,
               'title': 'Profile settings',
               'year': datetime.now().year,
               'user_form': user_form,
               'password_form': password_form,
               }

    #render page and send context
    return render(request, 'app/user/profilesettings.html', context)


@login_required(login_url='login')
def profile(request, username, groupid=None, noticeid=None):
    """ Renders the profile page -- this view handle both 
        if the user own this profile or its belongs to another user """

    login_user = get_user(request)  # get the user from session
    user = User.objects.get(username=username)  # get the given user

    # block check (if one of both blocked the other one --> redirect to not found page)
    you_block_this_user = user.block_from_user.filter(to_user=login_user)
    user_blocked_you = login_user.block_from_user.filter(to_user=user)
    if user_blocked_you or you_block_this_user:
        return redirect('notFound')

    friends = models.Friends.objects.filter(user1=user)  # friends for this user
    
    ''' forms usef in this view ''' 
    user_form = forms.UserChangeForm(instance=user) # this form to update user info.
    password_form = forms.PasswordChangeForm(user=request.user)  # this form to change user password  
    profile_form = forms.UserProfileChangeForm() # and this form to change profile info.

    # check if the request given by "profile owner"
    profile_owner = False
    if user == login_user:
        profile_owner = True

    #make the given notification read     
    if noticeid is not None:
        forms.make_notice_read(noticeid)

    if request.method == 'POST':
        # change user info. request 
        if request.POST.get("user_info") == 'true':
            user_form = forms.UserChangeForm(request.POST, instance=user) #get data
            if user_form.is_valid(): #check form validation 
                user_form.save()    
                return redirect('profile', user) 

        # change user password request 
        elif request.POST.get("user_pass") == 'true':
            password_form = forms.PasswordChangeForm(
                user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                # to keep user logged in after change password
                update_session_auth_hash(request, user)
                #to home page (can't redirect to the same page till complete auth process)
                return redirect('home') 

        # change/update user picture request
        elif request.POST.get("user_photo") == 'true':
            profile_form = forms.UserProfileChangeForm(
                request.POST, request.FILES, instance=user.user_profile) #get uploaed file
            if profile_form.is_valid():
                 #save image (image saved in computer server only its path save to DB)
                user_profile = profile_form.save()

                #to save image in DB (Binary field) ---- """ we can skip this step """
                path = user_profile.pic_path.path  # get image path
                profile_id = user_profile.user.id  # get profile id
                profile_form.change_user_photo(profile_id, path)  # the  image it self

        # remove user picture request
        elif request.POST.get("remove_photo") == 'true':
            profile_form.remove_photo(username)
 
        # send friend request
        elif request.POST.get("add_friend") == 'true':
            profile_form.add_friend(login_user, user)

        # cancel friend request (sender)
        elif request.POST.get("cancel_request") == 'true':
            profile_form.cancel_request(login_user, user)

        # delete friend request (receiver)
        elif request.POST.get("delete_request") == 'true':
            profile_form.delete_request(login_user, user)

        # accept friend request 
        elif request.POST.get("confirm_request") == 'true':
            profile_form.confirm_request(login_user, user)

        # delete friend request 
        elif request.POST.get("delete_friend") == 'true':
            profile_form.delete_friend(login_user, user)

        #block user request 
        elif request.POST.get("block_user") == 'true':
            profile_form.block_user(login_user, user)
            return redirect('/')

        # leaving group request 
        elif groupid is not None:
            profile_form.remove_group(user, groupid)

    context = {
        'user2': user,
        'friends': friends,
        'password_form': password_form,
        'profile_owner': profile_owner,
        'user_form': user_form,
        'profile_form': profile_form,
        'title': 'profile',
        'year': datetime.now().year,
    }
    return render(request, 'app/user/profile.html', context)


''''''
''' ===========================> group views <=========================== '''
''''''


@login_required(login_url='login')
def CreateGroup(request):
    """ render create group page """

    user = get_user(request)  # get user from session

    if request.method == 'POST':
        form = forms.CreateGroup(request.POST) #get entered data

        if form.is_valid():
            group_instance = form.save(user)  # get the model and save the form
            form.save_user(group_instance, user)  # save creator id

            #redirect to a page which user can add members to group or skip this
            return redirect('addGroupMembers', group_instance.id) 
    else:
        form = forms.CreateGroup() #send empty form if request is get
        
    return render(request, 'app/group/creategroup.html',
                  {'form': form,
                   'title': 'Create group',
                   'year': datetime.now().year,
                   })


@login_required(login_url='login')
def AddGroupMembers(request, groupid=None, userid=None):
    """ render add group members page """

    user = get_user(request)  # get user from session
    group = models.Group.objects.filter(pk=groupid).first()  # get group object

    #get list of user friends 
    friends = models.Friends.objects.filter(user1=user)  # get the relation 
    users = User.objects.none() 
    for friend in friends: #get friend user objects
        users |= User.objects.filter(pk=friend.user2.id)

    form = forms.AddGroupMembers() #create empty form 
    template = 'app/group/add_group_members.html'  #template path 
    context = {'form': form,
               'group': group,
               'users': users,
               'title': 'Add group group',
               'year': datetime.now().year, }

    if request.method == 'POST':
        # for search user request
        if request.POST.get("search_user") == 'true':
            
            form = forms.AddGroupMembers(request.POST) #get search text

            if form.is_valid():
                search = form.save() #save search text (we can use it as a search history)
                #seaching in DB using ""username"" 
                if search.search_text != "":  
                    users = User.objects.filter(username=search.search_text)
                    #we don't use the predefined context list cause 'users' has changed
                    return render(request, template, {'form': form,
                                                      'group': group,
                                                      'users': users,
                                                      'title': 'Add group members',
                                                      'year': datetime.now().year, })

        # for add member request 
        elif request.POST.get("add_user") == 'true':
            form.add_user(group, userid)

        # for remove member request
        elif request.POST.get("remove_user") == 'true':
            form.remove_user(group, userid)

    return render(request, template, context)


@login_required(login_url='login')
def ViewGroup(request, groupid, userid=None, noticeid=None):
    """ for group page """

    group = models.Group.objects.filter(pk=groupid).first()  # get group object
    group_members = group.members.all() #get its members
    user = get_user(request)  # get user from session

    #check if the user is a group admin or not 
    group_owner = False
    if group.creator.id == user.id:
        group_owner = True
    
    #make the given notification read     
    if noticeid is not None:
        forms.make_notice_read(noticeid)

    form = forms.CreateGroup(instance=group)  # to update group info.
    member_form = forms.AddGroupMembers()  # to add or remove members
    img_form = forms.UpdateGroupImage(instance=group)  # to upload photo

    template = 'app/group/group.html'

    if request.method == 'POST':
        # for update group info request
        if request.POST.get("update_group") == 'true':
            form = forms.CreateGroup(request.POST, instance=group)
            if form.is_valid():
                group = form.save()
                return redirect('viewGroup', groupid=group.id)

        # for update/upload group picture request
        if request.POST.get("update_group_img") == 'true':
            img_form = forms.UpdateGroupImage(
                data=request.POST, files=request.FILES, instance=group)
            if img_form.is_valid():
                group = img_form.save()
                path = group.pic_path.path
                img_form.save_group_pic(group.id, path)

        # for remove group member request
        if request.POST.get("remove_user") == 'true':
            member_form.remove_user(group, userid)
        
        # remove group picture request 
        if request.POST.get("remove_photo") == 'true':
            img_form.remove_photo(groupid)
            #instead of redirect update group object
            group = models.Group.objects.filter(pk=groupid).first()

        # remove group request (permanently deletion)
        if request.POST.get("remove_group") == 'true':
            img_form.remove_group(groupid)
            return redirect('/') #back to home page 

        # join call request - if group call running ======> (may be deleted)
        if request.POST.get("join_call") == 'true':
            return redirect('groupCall', group.id)

    context = {'form': form,
               'members': group_members,
               'group': group,
               'img_form': img_form,
               'group_owner': group_owner,
               'title': 'group',
               'year': datetime.now().year, }

    return render(request, template, context)


''''''
''' ===========================> audio group views <=========================== '''
''''''


@login_required(login_url='login')
def GroupCall(request, groupid):
    """ render group call page """

    ip = '10.101.248.46' #static ip to run this call
    group = models.Group.objects.filter(pk=groupid).first()  # get group from given id
    user = get_user(request)  # get user from session
    group_member = models.group_members.objects.filter(
        user=user, group=group).first() #get the relation between user and group

    if not request.POST:

        # Join call request
        if group_member.in_call == 0 and group.call_state != 0:  
            group_member.in_call = 1  # change call state for user
            group_member.save()
            # create client for request join
            Client.Client(ip, group.call_state, group_member)

        # start call request
        elif group.call_state == 0:  
            server = Server.Server(ip, group)  # establish call server

            ''' generate unique invite code include ip and group id
                (user would use it in desktop app to join call) '''
            hash_fn = basehash.base36() #use base hash to encrypt id & ip 
            sp = ip.split('.') #remove dots in ip
            invite_code = hash_fn.hash(sp[0]) + 'z' + hash_fn.hash(sp[1]) + 'z' + hash_fn.hash(
                sp[2]) + 'z' + hash_fn.hash(sp[3]) + 'z' + hash_fn.hash(groupid) #final code 
            
            #update group object 
            group.call_state = server.port  # change call state for group
            group.invite_code = invite_code 
            group.call_start_at = timezone.now()
            group.save() 

            # change call state for host user
            group_member.in_call = 1
            group_member.save()
            Client.Client(ip, server.port, group_member)  # create client for host

    if request.POST:

        ''' end group call request '''
        if request.POST.get("end_call") == 'true':
            group.call_state = 0  # change group call state
            group.invite_code = 0
            group.save()
            # change all group members in call state to zero
            for member in group.members.filter():
                group_member = models.group_members.objects.filter(
                    user=member, group=group).first()
                group_member.in_call = 0
                group_member.save()
            return redirect('viewGroup', groupid=group.id) #redirect to group page

        ''' leave group call request ''' 
        if request.POST.get("leave_call") == 'true':
            # change member in call state to zero
            group_member = models.group_members.objects.filter(
                user=user, group=group).first()
            group_member.in_call = 0
            group_member.save()
            return redirect('viewGroup', groupid=group.id) #redirect to group page

    #send user to call page, send required contexts to this page    
    return render(request, 'app/group/group_call.html',
                  {'group': group,
                   'group_member': group_member,
                   'ip': ip,
                   'title': 'create call',
                   'year': datetime.now().year})


@login_required(login_url='login')
def UploadGroupAudio(request, groupid):
    """ render uploading group audio page """

    group = models.Group.objects.filter(pk=groupid).first() # get group from given ID
    user = get_user(request)                                # get user from session
    error = 0 #change to 1 => when form is invaild to detect error

    if request.method == 'POST':
        form = forms.UploadGroupAudio(request.POST, request.FILES) #get the uploaded file 
        if form.is_valid():
            # get the model and save the form
            instance = form.save(commit=False)
            instance.group = group
            instance.state = 0  #state 0 mean file is upload (state change for each nlp process)
            if not instance.title:  # default title if user leave title blank
                instance.title = group.name + '-' + \
                    instance.call_date.strftime("%Y/%m/%d, %H:%M:%S")
            instance.save() #save this record in db

            #start exectue NLP processes in background
            tasks.nlp_thread(instance.id, user)  
            
            #redirect to group list page while processing
            return redirect('group_meetings')       
        else:
            error = 1
    else:
        form = forms.UploadGroupAudio() #if request get send empty form 

    #render page and send requried contexts
    return render(request, 'app/audio_file/upload_group_audio.html',
                  {'form': form,
                   'group': group,
                   'title': 'Upload group call',
                   'year': datetime.now().year,
                   'error': error,
                   })


@login_required(login_url='login')
def GroupAudios(request, noticeid=None):
    """ this view to render group meetings list """
    user = get_user(request)  # get user from session
    user_groups = models.Group.objects.filter(
        members=user)  # get all groups inculde this user
    
    #make the given notification read     
    if noticeid is not None:
        forms.make_notice_read(noticeid)

    # get all group audio for each group
    calls = models.Audio_group_call.objects.none()
    for group in user_groups:
        calls |= models.Audio_group_call.objects.filter(group=group)

    return render(request, 'app/audio_file/group_audios.html',
                  {'calls': calls,
                   'title': 'group calls',
                   'year': datetime.now().year,
                   })


def refresh_audio_table(request):
    """ this view to refresh group meetings table"""

    user = get_user(request)  # get user from session
    user_groups = models.Group.objects.filter(
        members=user)  # get all groups inculde this user

    # get all group audio for each group
    calls = models.Audio_group_call.objects.none()
    for group in user_groups:
        calls |= models.Audio_group_call.objects.filter(group=group)

    return render(request, 'app/audio_file/refresh_group_audios.html', {'calls': calls})


@login_required(login_url='login')
def GroupAudio(request, audio_id, noticeid=None):
    """ this page to view all group meeting data (voice, nlp outputs) """
    call = models.Audio_group_call.objects.filter(pk=audio_id).first()
    
    #make the given notification read     
    if noticeid is not None:
        forms.make_notice_read(noticeid)

    if request.method == 'POST':
        # Download speech to text file request
        if request.POST.get("download_stt") == 'true':
            response = HttpResponse(open(call.stt_file_path.path, 'rb').read())
            response['Content-Type'] = 'text/plain'
            response['Content-Disposition'] = 'attachment; filename=Speech-to-text.txt'
            return response
        # Download meeting summary file request
        elif request.POST.get("download_summary") == 'true':
            response = HttpResponse(open(call.sum_file_path.path, 'rb').read())
            response['Content-Type'] = 'text/plain'
            response['Content-Disposition'] = 'attachment; filename=meeting-summary.txt'
            return response

    return render(request, 'app/audio_file/group_audio.html',
                  {'call': call,
                   'title': 'Meeting',
                   'year': datetime.now().year,
                   })
