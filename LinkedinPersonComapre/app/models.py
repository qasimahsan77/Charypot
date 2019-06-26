"""
Definition of models.
"""

from django.db import models

# Create your models here.
class Profile(models.Model):
    name=models.CharField(max_length=300,blank=True,null=True)
    occupation=models.CharField(max_length=300,blank=True,null=True)
    workhistory=models.CharField(max_length=300,blank=True,null=True)
    profileurl=models.CharField(max_length=300,blank=True,null=True)
    headline=models.CharField(max_length=300,blank=True,null=True)
    location=models.CharField(max_length=300,blank=True,null=True)
    industry=models.CharField(max_length=300,blank=True,null=True)
    summary=models.CharField(max_length=300,blank=True,null=True)
    description=models.TextField(max_length=500,blank=True,null=True)
    schoolname=models.CharField(max_length=300,blank=True,null=True)
    companyname=models.CharField(max_length=300,blank=True,null=True)
    imageurl=models.URLField(max_length=300,blank=True,null=True)
    skills=models.TextField(max_length=400,blank=True,null=True)
  
class TwitterProfile(models.Model):
    twitter_profile=models.TextField(max_length=300,blank=True,null=True)
    twitter_username=models.TextField(max_length=500,blank=True,null=True)
    profile_id=models.TextField(max_length=300,blank=True,null=True)
    profile_location=models.TextField(max_length=300,blank=True,null=True)
    imageurl=models.URLField(max_length=300,blank=True,null=True)
    latest_post_link=models.URLField(max_length=400,blank=True,null=True)