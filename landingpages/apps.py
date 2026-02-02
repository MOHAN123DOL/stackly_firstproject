from django.apps import AppConfig


class LandingConfig(AppConfig):
    name = "landingpages"

    def ready(self):
        import landingpages.signals
