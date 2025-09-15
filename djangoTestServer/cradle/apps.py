from django.apps import AppConfig

class CradleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cradle'

    def ready(self):
        from .mqtt_handler import connect_mqtt
        import threading
        threading.Thread(target=connect_mqtt, daemon=True).start()
