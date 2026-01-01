from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

# Register your models here.
from .models import ConfigModel

@admin.register(ConfigModel)
class ConfigModelAdmin(ImportExportModelAdmin):
    list_display = ('id', 'topMenuEnabled', 'customerServicePhone')
    search_fields = ('id', 'customerServicePhone')
