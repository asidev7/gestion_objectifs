from django.apps import AppConfig


class ObjectifsConfig(AppConfig):
    name = 'objectifs'
    
    def ready(self):
        import objectifs.signals  # <- important pour activer le signal

