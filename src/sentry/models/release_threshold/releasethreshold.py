from django.db import models
from django.utils import timezone

from sentry.backup.scopes import RelocationScope
from sentry.db.models import FlexibleForeignKey, Model, region_silo_only_model
from sentry.db.models.fields.bounded import BoundedPositiveIntegerField
from sentry.models.release_threshold.constants import ReleaseThresholdType, TriggerType


@region_silo_only_model
class ReleaseThreshold(Model):
    __relocation_scope__ = RelocationScope.Excluded

    threshold_type = BoundedPositiveIntegerField(choices=ReleaseThresholdType.as_choices())
    trigger_type = BoundedPositiveIntegerField(choices=TriggerType.as_choices())

    value = models.IntegerField()
    window_in_seconds = models.IntegerField()

    project = FlexibleForeignKey("sentry.Project", db_index=True)
    environment = FlexibleForeignKey("sentry.Environment", null=True, db_index=True)
    date_added = models.DateTimeField(default=timezone.now)
