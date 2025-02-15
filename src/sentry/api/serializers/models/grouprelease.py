from collections import namedtuple
from datetime import timedelta
from typing import Dict, List

from django.utils import timezone

from sentry import tsdb
from sentry.api.serializers import Serializer, register, serialize
from sentry.models import GroupRelease, Project, Release
from sentry.tsdb.base import TSDBModel

StatsPeriod = namedtuple("StatsPeriod", ("segments", "interval"))


@register(GroupRelease)
class GroupReleaseSerializer(Serializer):
    def get_attrs(self, item_list, user):
        release_list = list(Release.objects.filter(id__in=[i.release_id for i in item_list]))
        releases = {r.id: d for r, d in zip(release_list, serialize(release_list, user))}

        result = {}
        for item in item_list:
            result[item] = {"release": releases.get(item.release_id)}
        return result

    def serialize(self, obj, attrs, user):
        return {
            "release": attrs["release"],
            "environment": obj.environment,
            "firstSeen": obj.first_seen,
            "lastSeen": obj.last_seen,
        }


class GroupReleaseWithStatsSerializer(GroupReleaseSerializer):
    STATS_PERIODS = {
        "24h": StatsPeriod(24, timedelta(hours=1)),
        "30d": StatsPeriod(30, timedelta(hours=24)),
    }

    def __init__(self, since=None, until=None):
        self.since = since
        self.until = until

    def get_attrs(self, item_list, user):
        attrs = super().get_attrs(item_list, user)

        tenant_ids = (
            {
                "organization_id": Project.objects.get_from_cache(
                    id=item_list[0].project_id
                ).organization_id
            }
            if item_list
            else None
        )

        items: Dict[str, List[str]] = {}
        for item in item_list:
            items.setdefault(item.group_id, []).append(item.id)
            attrs[item]["stats"] = {}

        for key, (segments, interval) in self.STATS_PERIODS.items():
            until = self.until or timezone.now()
            since = self.since or until - (segments * interval)

            try:
                stats = tsdb.backend.get_frequency_series(
                    model=TSDBModel.frequent_releases_by_group,
                    items=items,
                    start=since,
                    end=until,
                    rollup=int(interval.total_seconds()),
                    tenant_ids=tenant_ids,
                )
            except NotImplementedError:
                # TODO(dcramer): probably should log this, but not worth
                # erring out
                stats = {}

            for item in item_list:
                attrs[item]["stats"][key] = [
                    (k, v[item.id]) for k, v in stats.get(item.group_id, {})
                ]
        return attrs

    def serialize(self, obj, attrs, user):
        result = super().serialize(obj, attrs, user)
        result["stats"] = attrs["stats"]
        return result
