from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import StoreStatus, StoreTime

class Command(BaseCommand):
    help = 'Toggle store status'

    def handle(self, *args, **options):
        today = datetime.today().strftime('%A')
        current_time = timezone.now().time()

        schedule = StoreTime.objects.get(day = today.upper())
        store_status = StoreStatus.objects.get(id=1)

        if schedule.open_time <= current_time < schedule.closei_tme \
              and store_status.is_open == False:
            store_status.is_open = True
            self.stdout.write(self.style.SUCCESS('Store open'))

        if schedule.close_time <= current_time > schedule.open_time \
              and store_status.is_open == True:
            store_status.is_open = False
            self.stdout.write(self.style.SUCCESS('Store close'))

        store_status.save()
        self.stdout.write(self.style.SUCCESS('Store status updated'))
