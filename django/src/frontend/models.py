from django.db import models
from django.contrib.auth.models import User

# Add any user specific fields to this, and all User-objects will have a 'get_profile()' method
# that you can use to retrieve this set of data.
# NB use the 'profile' property being added to the User object, as this will create a profile
# if one does not already exist. The 'get_profile()' method will fail if a profile does not exist
# (and is therefore always safe, but might throw an exception if user has no profile set up.)

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    name = models.CharField(max_length=70, blank=True)

class Silo(models.Model):
    silo = models.CharField(max_length=50)

class Dataset(models.Model):
    silo = models.ForeignKey(Silo, unique=True)
    name = models.CharField(max_length=100, blank=True)

# Create the profile on reference
User.profile = property(lambda u: UserProfile.objects.get_or_create(user=u)[0])
