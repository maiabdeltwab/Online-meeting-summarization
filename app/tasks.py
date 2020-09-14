""" back ground processing tasks """

import threading

from django.utils import timezone
from notifications.signals import notify

import app.forms as forms
import app.models as models

def nlp_tasks(record_id, user):
    """
          This method take the audio meeting ip and the user obj
      ==> apply all NLP processes and raise notification to inform user when compelte
    """
    instance = models.Audio_group_call.objects.filter(pk=record_id).first() #get meeting instance
    form = forms.UploadGroupAudio(instance=instance) #note: define this form to only use its methods

    path = instance.audio_file_path.path  # get file path
    record_id = instance.id  # get model id

    # update the record to include the audio it self (Binary data) ===> we can skip this step
    # form.save_group_audio(record_id, path)
    users = instance.group.members.filter()
    notify.send(user, recipient=users, verb='upload_meeting', target=instance)

    #update state to (1) ==> to inform the user "stt is running now"
    instance.state = 1
    instance.save()
    #apply speech to text algorithm
    stt_only, stt_with_speakers = form.stt_voice_recog(record_id, path) #return stt files path

    instance.stt_file_path = stt_with_speakers  #save it in DB

    #update state to (2) ==> to inform the user text summarization is running now
    instance.state = 2
    instance.save()

    #apply the text summarization algorithm
    instance.sum_file_path = form.text_summarization(record_id, stt_only)
    instance.finished_at = timezone.now

    #update state to (3) ==> to inform the user that NLP processing has finished
    instance.state = 3
    instance.save()
    #create a notification object to inform the user
    notify.send(user, recipient=users, verb='finish_nlp', target=instance)



def nlp_thread(record_id, user):
    """
          This method take the audio meeting ip and the user obj
          ==> run the nlp_tasks function as a thread
    """
    threading.Thread(target=nlp_tasks, args=(record_id, user)).start()
