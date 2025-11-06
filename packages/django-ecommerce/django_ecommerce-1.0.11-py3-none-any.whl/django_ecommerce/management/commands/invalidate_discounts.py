from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import F
from django_ecommerce.models import Discount


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        now = timezone.now()

        # ACTIVATIONS
        to_activate = Discount.objects.filter(
            start_date__lte=now,
            end_date__gt=now,
        ).exclude(last_activation_run__gte=F("start_date"))

        for d in to_activate:
            self.invalidate_for_discount(d)
            d.last_activation_run = now
            d.save(update_fields=["last_activation_run"])

        # DEACTIVATIONS
        to_deactivate = Discount.objects.filter(end_date__lte=now).exclude(
            last_deactivation_run__gte=F("end_date")
        )

        for d in to_deactivate:
            self.invalidate_for_discount(d)
            d.last_deactivation_run = now
            d.save(update_fields=["last_deactivation_run"])

    def invalidate_for_discount(self, discount):
        # Todo: invalidate cache for products and categories affected by the discount
        cache.clear()
