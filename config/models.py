from django.db import models
import uuid

# Create your models here.
class ConfigModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topMenuEnabled = models.BooleanField(default=True)
    termsUrl = models.CharField(max_length=255, blank=True,null=True)
    privacyUrl = models.CharField(max_length=255, blank=True,null=True)
    kvkkUrl = models.CharField(max_length=255, blank=True,null=True)
    marketingInfoUrl = models.CharField(max_length=255, blank=True,null=True)
    googleMapsApiKeyAndroid = models.CharField(max_length=255, blank=True,null=True)
    googleMapsApiKeyIos = models.CharField(max_length=255, blank=True,null=True)
    customerServicePhone = models.CharField(max_length=255, blank=True,null=True)
    customerServiceWhatsapp = models.CharField(max_length=255, blank=True,null=True)
    preliminaryInfoUrl = models.CharField(max_length=255, blank=True,null=True)
    distanceSalesAgreementUrl = models.CharField(max_length=255, blank=True,null=True)

    def __str__(self):
        return f"Config: {self.id}"

    class Meta:
        verbose_name = "Configuration"
        verbose_name_plural = "Configurations"
