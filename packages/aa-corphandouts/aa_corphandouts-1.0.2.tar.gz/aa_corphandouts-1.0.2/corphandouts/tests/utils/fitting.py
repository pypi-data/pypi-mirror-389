from fittings.models import Fitting, FittingItem

from eveuniverse.models import EveType


def create_sabre_fitting() -> Fitting:
    fit = Fitting.objects.create(
        name="Test fit",
        ship_type=EveType.objects.get(id=22456),
        ship_type_type_id=22456,
    )

    for i in range(6):
        __add_item_to_fit(fit, f"HiSlot{i}", type_id=2873)  # 125mm II
    __add_item_to_fit(fit, "HiSlot6", 22782)  # Sphere launcher
    __add_item_to_fit(fit, "HiSlot7", 20565)  # Cloak

    for i in range(2):
        __add_item_to_fit(fit, f"MedSlot{i}", type_id=8517)  # MSE
    __add_item_to_fit(fit, "MedSlot2", type_id=35658)  # 5mn
    __add_item_to_fit(fit, "MedSlot3", type_id=40758)  # scram

    for i in range(2):
        __add_item_to_fit(fit, f"LoSlot{i}", type_id=2605)  # Nanos
        __add_item_to_fit(fit, f"RigSlot{i}", type_id=31165)  # Hypers

    __add_item_to_fit(fit, "Cargo", type_id=12608, quantity=2000)  # Hail S
    __add_item_to_fit(fit, "Cargo", type_id=12625, quantity=1000)  # Barrage S

    return fit


def __add_item_to_fit(
    fit: Fitting, flag: str, type_id: int, quantity: int | None = None
):
    FittingItem.objects.create(
        fit=fit,
        flag=flag,
        quantity=quantity or 1,
        type_fk=EveType.objects.get(id=type_id),
        type_id=type_id,
    )
