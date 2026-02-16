from rest_framework import serializers
from .models import Service

class ServiceSerializer(serializers.ModelSerializer):
    pricing = serializers.SerializerMethodField()
    active = serializers.BooleanField(source='is_active')
    # id field is already UUID by default model serializer behavior

    class Meta:
        model = Service
        fields = ['id', 'slug', 'name', 'active', 'image', 'description', 'pricing', 'show_price']

    def get_pricing(self, obj):
        return {
            "base_fee": obj.base_fee,
            "per_km": obj.per_km,
            "free_distance": obj.free_distance
        }
