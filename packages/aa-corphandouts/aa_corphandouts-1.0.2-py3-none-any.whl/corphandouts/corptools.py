"""Integration with the corptools application"""

from corptools.models import CorpAsset, CorporationAudit, EveLocation

from django.db.models import Q, QuerySet

from allianceauth.services.hooks import get_extension_logger

logger = get_extension_logger(__name__)


def get_assets_corporation_division(
    corporation: CorporationAudit, location: EveLocation, hangar_division: int
) -> QuerySet[CorpAsset]:
    """Returns a queryset of corporation assets in the specified hangar and location"""

    corp_assets = CorpAsset.objects.filter(corporation=corporation)
    asset_locations = corp_assets.filter(location_name_id=location.location_id)
    corp_assets = corp_assets.filter(
        Q(location_name_id=location.location_id)
        | Q(location_id__in=asset_locations.values_list("item_id"))
        | Q(location_id=location.location_id)
    )

    return corp_assets.filter(location_flag=f"CorpSAG{hangar_division}")


def get_ship_fit(ship_item_id: int) -> QuerySet[CorpAsset]:
    """Returns all known items linked to this ship id"""

    return CorpAsset.objects.filter(location_id=ship_item_id)
