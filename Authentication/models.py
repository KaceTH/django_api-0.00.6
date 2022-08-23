from datetime import datetime, timedelta
from django.core.mail import send_mail
import pytz
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Create your models here.

class TimeStampedModel(models.Model):
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractUser):

    USER_TYPES = (
        (1, 'Student'),
        (2, 'Teacher'),
        (3, 'Parents')
    )
    
    name = models.CharField(max_length=50, blank=True)
    email = models.CharField(max_length=40, blank=True)
    school = models.CharField(max_length=100, default="Unnamed")
    
    user_type = models.IntegerField(choices=USER_TYPES, default=1, blank=True)

    grade_number = models.IntegerField(default=0)
    class_number = models.IntegerField(default=0)
    student_number = models.IntegerField(default=0)

    is_verificated = models.BooleanField(default=False, blank=True)

    def __str__(self):
        return self.username


class Verification(TimeStampedModel) :
    author = models.ForeignKey(
        User, 
        models.CASCADE,
        "author", 
        blank=False,
        null=False,
    )
    code = models.IntegerField(null=False)
    expiration_date = models.TimeField(blank=True, null=True)

    def set_end_date(self):
        self.expiration_date = datetime.utcnow() + timedelta(days=0, minutes=10)
        self.save()
        return 

    def is_end_date(self):
        utc=pytz.UTC
        if datetime.utcnow().time() > self.expiration_date:
            return True
        return False

    def send_verification(self) :
        name = 'User Email Authentication'
        message = f'This is the code for verification {self.code}'
        send_mail(
            name, #title
            message, #message
            settings.EMAIL_HOST_USER, #from
            [self.author.email], #to
        )

