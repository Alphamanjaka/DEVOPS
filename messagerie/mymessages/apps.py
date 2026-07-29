from django.apps import AppConfig


class MymessagesConfig(AppConfig):
    name = 'mymessages'

    def ready(self):
        import mymessages.signals  # noqa
