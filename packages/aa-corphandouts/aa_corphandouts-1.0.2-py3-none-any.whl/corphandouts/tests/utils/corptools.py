from corptools.models import CorpAsset, CorporationAudit, EveItemType, EveLocation

from allianceauth.eveonline.models import EveCorporationInfo

CORPORATION_ID = 109299958
SHIP_ITEM_ID = 1042868888363


def _create_corptools_corporation():
    """Creates the C C P corporation in corptools"""
    corporation_info = EveCorporationInfo(
        corporation_id=CORPORATION_ID
    ).update_corporation()
    CorporationAudit.objects.create(corporation=corporation_info)


def corptools_create_fitted_sabre(
    location: EveLocation, corporation: CorporationAudit
) -> CorpAsset:
    """
    Adds a fitted sabre in corp hangar 1
    Returns the sabre Asset
    """
    corporation_id = corporation.corporation.corporation_id
    sabre = __create_corptools_corp_asset(
        True,
        SHIP_ITEM_ID,
        "CorpSAG1",
        location.location_id,
        1,
        22456,
        corporation_id,
        "test sabre",
    )
    sabre_location = EveLocation.objects.create(
        location_name="sabre location", location_id=SHIP_ITEM_ID
    )
    location_id = sabre_location.location_id
    for i in range(6):
        __create_corptools_corp_asset(
            True,
            100 + i,
            location_flag=f"HiSlot{i}",
            location_id=location_id,
            quantity=1,
            type_id=2873,
            corporation_id=corporation_id,
        )  # 125mm AC
    __create_corptools_corp_asset(
        True,
        110,
        location_flag="HiSlot6",
        location_id=location_id,
        quantity=1,
        type_id=22782,
        corporation_id=corporation_id,
    )  # Sphere launcher
    __create_corptools_corp_asset(
        True,
        120,
        location_flag="HiSlot7",
        location_id=location_id,
        quantity=1,
        type_id=20565,
        corporation_id=corporation_id,
    )  # Cloak

    for i in range(2):
        __create_corptools_corp_asset(
            True,
            200 + i,
            location_flag=f"MedSlot{i}",
            location_id=location_id,
            quantity=1,
            type_id=8517,
            corporation_id=corporation_id,
        )  # Compact MSE
    __create_corptools_corp_asset(
        True,
        210,
        location_flag="MedSlot2",
        location_id=location_id,
        quantity=1,
        type_id=35658,
        corporation_id=corporation_id,
    )  # 5mn
    __create_corptools_corp_asset(
        True,
        220,
        location_flag="MedSlot3",
        location_id=location_id,
        quantity=1,
        type_id=40758,
        corporation_id=corporation_id,
    )  # Scram

    for i in range(2):
        __create_corptools_corp_asset(
            True,
            300 + i,
            location_flag=f"LoSlot{i}",
            location_id=location_id,
            quantity=1,
            type_id=2605,
            corporation_id=corporation_id,
        )  # Nanos
        __create_corptools_corp_asset(
            True,
            400 + i,
            location_flag=f"RigSlot{i}",
            location_id=location_id,
            quantity=1,
            type_id=31165,
            corporation_id=corporation_id,
        )  # Hypers

    __create_corptools_corp_asset(
        False,
        500,
        location_flag="Cargo",
        location_id=location_id,
        quantity=2000,
        type_id=12608,
        corporation_id=corporation_id,
    )  # Hail
    __create_corptools_corp_asset(
        False,
        501,
        location_flag="Cargo",
        location_id=location_id,
        quantity=1000,
        type_id=12625,
        corporation_id=corporation_id,
    )  # Barrage

    return sabre


def corptools_create_sabre_stack(location: EveLocation, corporation: CorporationAudit):
    """Creates a stack of sabres"""
    corporation_id = corporation.corporation.corporation_id
    return __create_corptools_corp_asset(
        False,
        SHIP_ITEM_ID,
        "CorpSAG1",
        location.location_id,
        3,
        22456,
        corporation_id,
    )


def __create_corptools_corp_asset(
    singleton: bool,
    item_id: int,
    location_flag: str,
    location_id: int,
    quantity: int,
    type_id: int,
    corporation_id: int,
    item_name: str = None,
) -> CorpAsset:
    return CorpAsset.objects.create(
        singleton=singleton,
        item_id=item_id,
        location_flag=location_flag,
        location_id=location_id,
        location_type="Station",
        quantity=quantity,
        type_id=type_id,
        type_name=EveItemType.objects.get_or_create_from_esi(type_id)[0],
        location_name=EveLocation.objects.get(location_id=location_id),
        corporation=CorporationAudit.objects.get(
            corporation__corporation_id=corporation_id
        ),
        name=item_name,
    )
