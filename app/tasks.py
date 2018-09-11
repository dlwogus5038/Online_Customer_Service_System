from celery import task
from .models import *
import time


@task()
def delete_expired():
    data = VerificationData.objects.all()
    now = int(time.mktime(timezone.now().timetuple()))
    for datum in data:
        created_at = int(time.mktime(datum.created_at.timetuple()))
        if now - created_at > 1800:
            datum.delete()
    return "Deleted Expired Verification Data"


@task()
def initialize_staff_score():
    staffs = MyUser.objects.filter(is_admin=False, is_company=False)
    staffs.update(chatting_time=0, chatting_num=0, chatting_score=0)

    return 'initialized staff score'
