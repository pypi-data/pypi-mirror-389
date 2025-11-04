from django.contrib import admin
from .models import WhatsAppCloudApiBusiness, MetaApp
# Register your models here.

admin.site.register(WhatsAppCloudApiBusiness)
admin.site.register(MetaApp)

# Import webhooks admin registrations so they are discovered
try:
    from .whatsapp_cloud_api.webhooks import admin as webhooks_admin  # noqa: F401
except Exception:
    logging.getLogger(__name__).exception("Failed to import webhooks admin")


    

    
