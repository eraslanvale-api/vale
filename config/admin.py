from django.contrib import admin

# Register your models here.
from .models import ConfigModel

admin.site.register(ConfigModel)
