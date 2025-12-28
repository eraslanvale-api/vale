from rest_framework import serializers
from .models import ConfigModel

class ConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfigModel
        fields = '__all__'
