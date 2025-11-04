from django.core.management.base import BaseCommand
from wise.internal.health_check import health_check as hc


class Command(BaseCommand):
    help = "Check health of depended services"

    def handle(self, *args, **options):
        if hc.check_all():
            self.stdout("OK")
            exit(0)
        else:
            self.stderr("FAILED")
            exit(1)
