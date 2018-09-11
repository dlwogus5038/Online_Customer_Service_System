from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)
import random


class MyUserManager(BaseUserManager):
    def create_user(self, username, email, name, password=None):
        if not email:
            raise ValueError('Users must have an E-mail')

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            name=name
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_staff(self, username, name, email, is_active, process_num, company_code, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(
            email=self.normalize_email(email),
            username=username,
            name=name,
            company_code=company_code,
            is_active=eval(is_active),
            process_num=process_num
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_company(self, username, company_name, email, password=None):
        if not email:
            raise ValueError('User must have an Email address')
        user = self.model(
            email=email,
            company_name=company_name,
            username=username,
            is_company=True,
            process_num=0
        )
        users = self.all()
        num = 0
        while True:
            is_unique = True
            num = random.randint(20000, 65000)
            for my_user in users:
                if int(num) is int(my_user.company_code):
                    is_unique = False
            if is_unique:
                break
        user.company_code = num
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, name, password):
        user = self.create_user(
            username=username,
            name=name,
            email=self.normalize_email(email),
            password=password,
        )
        user.is_company = True
        user.is_admin = True
        user.is_verified = True
        user.save(using=self._db)
        return user


class MyUser(AbstractBaseUser):
    username = models.CharField(max_length=12, unique=True)
    name = models.CharField(max_length=10)
    email = models.EmailField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_company = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    company_code = models.IntegerField(default=0)
    is_set_faq = models.BooleanField(default=False)
    image = models.FileField(upload_to='./', verbose_name="图片", default='default_image.png')

    # Only Company
    company_name = models.CharField(max_length=255)
    max_waiting_time = models.IntegerField(default=180) #second
    linkman = models.CharField(max_length=20, default='')
    phonenumber = models.CharField(max_length=11, default='')
    chatterbot_image = models.FileField(upload_to='./', verbose_name="图片", default='chatterbot_default_image.png')
    chatterbot_nickname = models.CharField(max_length=20, default='自动回复机器人')

    # Only Staff
    nickname = models.CharField(max_length=20, default='客服人员')
    status = models.IntegerField(default=0)  # 0 means offline / 1 means online / 2 means on work / 3 means busy / 4 means step out
    process_num = models.IntegerField(default=1)  # maximum process number, company can modify it
    cur_process = models.IntegerField(default=0)  # current process number
    chatting_time = models.IntegerField(default=0)  # per day & 1 second = 1 time
    chatting_num = models.IntegerField(default=0)  # per day & 1 person = 1 num
    chatting_score = models.DecimalField(max_digits=10, decimal_places=3, default=0)  # per day & 1 time = 1 score & time/average time
    staff_ip = models.CharField(max_length=15, default="0.0.0.0")
    staff_port = models.CharField(max_length=6, default="0")

    objects = MyUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'name']

    def __str__(self):
        return self.username

    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin

    def get_image_url(self):
        return '%s%s' % (settings.MEDIA_URL, self.image)

    def get_chatterbot_image_url(self):
        return '%s%s' % (settings.MEDIA_URL, self.chatterbot_image)


class VerificationData(models.Model):
    username = models.CharField(max_length=12, unique=True)
    verification_code = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(default=timezone.now)


class ChatData(models.Model):
    staff = models.ForeignKey(MyUser)
    user_ip = models.CharField(max_length=15, default="0.0.0.0")
    user_port = models.CharField(max_length=6, default="0")
    Data = models.TextField()
    is_send = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)


class ChatRecord(models.Model):
    staff = models.ForeignKey(MyUser)
    user_IP = models.CharField(max_length=15, default='0.0.0.0')
    user_Port = models.CharField(max_length=6, default='0')
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(default=timezone.now)
    score = models.IntegerField(default = -1)
    address = models.CharField(max_length=50, default='暂无信息')
    chatting_time = models.CharField(max_length=20)


class ChatConnection(models.Model):
    staff = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    index = models.IntegerField(default=0)
    user_ip = models.CharField(max_length=15)
    user_port = models.CharField(max_length=6)
    staff_name = models.CharField(max_length=12)
    staff_ip = models.CharField(max_length=15)
    staff_port = models.CharField(max_length=6)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(default=timezone.now)


class ImageData(models.Model):
    user_IP = models.CharField(max_length=15, default='0.0.0.0')
    user_port = models.CharField(max_length=6)
    chat_index = models.IntegerField(default=0)
    image_name = models.CharField(max_length=100, default='')


class AnswerList(models.Model):
    company_code = models.IntegerField(default=0)
    answer = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)