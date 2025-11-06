"""Tasks."""

from collections import Counter

from celery import group, shared_task
from corptools.models import CorpAsset

from eveuniverse.models import EveType

from allianceauth.services.hooks import get_extension_logger

from corphandouts.corptools import get_assets_corporation_division, get_ship_fit
from corphandouts.models import (
    DoctrineReport,
    FittingCorrection,
    FittingReport,
    FittingToCorrect,
)

logger = get_extension_logger(__name__)


@shared_task()
def update_all_doctrine_reports():
    """Runs the update command on all doctrines"""
    doctrines = DoctrineReport.objects.all()
    logger.info("Running the update command on %d doctrines", doctrines.count())

    tasks = [update_doctrine_report.si(doctrine.id) for doctrine in doctrines]
    group(tasks).delay()


@shared_task()
def update_doctrine_report(doctrine_report_id: int):
    """
    Goes through corporation assets to check what fits need to be updated
    """
    logger.info("Updating doctrine report id %d", doctrine_report_id)
    doctrine_report = DoctrineReport.objects.get(id=doctrine_report_id)
    assets_in_corporation_division = get_assets_corporation_division(
        doctrine_report.corporation,
        doctrine_report.location,
        doctrine_report.corporation_hangar_division,
    )
    logger.debug(
        "%d assets fetched in the corporation division",
        assets_in_corporation_division.count(),
    )

    tasks = []
    for fitting_to_check in doctrine_report.fittings.all():
        fit_ship_type_id = fitting_to_check.fit.ship_type_type_id
        corporation_assets_to_check = assets_in_corporation_division.filter(
            type_id=fit_ship_type_id,
            singleton=True,
        )
        if regex_pattern := fitting_to_check.regex:
            logger.debug("Regex detected: %s")
            corporation_assets_to_check = corporation_assets_to_check.filter(
                name__regex=regex_pattern
            )

        item_ids_to_check = corporation_assets_to_check.values_list(
            "item_id", flat=True
        )
        logger.debug(
            "%d item with type id %d found %s",
            item_ids_to_check.count(),
            fit_ship_type_id,
            list(item_ids_to_check),
        )
        tasks.append(
            check_doctrine_fit.si(fitting_to_check.id, list(item_ids_to_check))
        )

    group(tasks).delay()


# pylint: disable = too-many-locals
@shared_task()
def check_doctrine_fit(fitting_report_id: int, ships_item_ids: list[int]):
    """
    Receives a list of item_ids that are in the hangar appropriate for this fitting.
    Then checks which of them are fitted correctly
    If they are not fitted correctly creates a new task that creates a fitting correction
    """
    logger.info("Updating fitting report id %d", fitting_report_id)
    logger.debug(ships_item_ids)
    fitting_report = FittingReport.objects.get(id=fitting_report_id)

    # Deletes existing corrections if any to overwrite
    FittingToCorrect.objects.filter(fit=fitting_report).delete()

    expected_fitting_items = fitting_report.fit.items.all()
    expected_fitting_counter = Counter(
        expected_fitting_items.filter(
            flag__regex=r"^(Hi|Med|Lo|Rig|SubSystem)Slot\d$"
        ).values_list("type_id", flat=True)
    )
    expected_cargo_counter = Counter(
        dict(
            expected_fitting_items.filter(flag="Cargo").values_list(
                "type_id", "quantity"
            )
        )
    )
    logger.debug(expected_fitting_counter)
    logger.debug(expected_cargo_counter)

    fit_ok_count = 0
    fits_to_fix = []

    for ship_item_id in ships_item_ids:
        logger.debug("Checking item id %d", ship_item_id)

        current_ship_items = get_ship_fit(ship_item_id)
        current_fitting_counter = Counter(
            current_ship_items.filter(
                location_flag__regex=r"^(Hi|Med|Lo|Rig|SubSystem)Slot\d$"
            ).values_list("type_id", flat=True)
        )
        # TODO Check the "AutoFit" flag items to move in cargo
        current_cargo_counter = Counter(
            dict(
                current_ship_items.filter(location_flag="Cargo").values_list(
                    "type_id", "quantity"
                )
            )
        )
        logger.debug(current_cargo_counter)
        current_fitting_counter.subtract(expected_fitting_counter)
        current_cargo_counter.subtract(expected_cargo_counter)
        logger.debug(current_fitting_counter)
        logger.debug(current_cargo_counter)

        # TODO write tests for this
        if any(current_fitting_counter.values()) or any(current_cargo_counter.values()):
            logger.info("%d fit is incorrect", ship_item_id)
            fits_to_fix.append(
                (ship_item_id, current_fitting_counter, current_cargo_counter)
            )
        else:
            logger.debug("%d fit is correct", ship_item_id)
            fit_ok_count += 1

    logger.debug("Ok ships: %d", fit_ok_count)
    fitting_report.ok_ships = fit_ok_count
    fitting_report.save()

    if not fits_to_fix:
        logger.info("All fits fitted correctly, exiting")
        return

    fitting_tasks = []
    for item_id, fitting_difference, cargo_difference in fits_to_fix:
        fitting_tasks.append(
            create_fitting_report.si(
                fitting_report_id, item_id, fitting_difference, cargo_difference
            )
        )
    group(fitting_tasks).delay()


@shared_task
def create_fitting_report(
    fitting_report_id: int, item_id, fitting_difference, cargo_difference
):
    """Creates the fitting report from the information gathered in the previous task"""
    logger.debug(
        "Creating fitting report %d %s %s %s",
        fitting_report_id,
        item_id,
        fitting_difference,
        cargo_difference,
    )
    fitting_report = FittingReport.objects.get(id=fitting_report_id)

    corp_asset = CorpAsset.objects.get(item_id=item_id)
    fitting_to_correct = FittingToCorrect.objects.create(
        fit=fitting_report,
        item_id=corp_asset.item_id,
        item_name=corp_asset.name,
    )
    corrections = []
    for type_id, amount in fitting_difference.items():
        if amount:
            amount = -amount
            eve_type, _ = EveType.objects.get_or_create_esi(id=type_id)
            corrections.append(
                FittingCorrection(
                    fit_to_correct=fitting_to_correct,
                    eve_type=eve_type,
                    correction=amount,
                    correction_type=FittingCorrection.CorrectionType.FITTING,
                )
            )
    for type_id, amount in cargo_difference.items():
        if amount:
            amount = -amount
            eve_type, _ = EveType.objects.get_or_create_esi(id=type_id)
            corrections.append(
                FittingCorrection(
                    fit_to_correct=fitting_to_correct,
                    eve_type=eve_type,
                    correction=amount,
                    correction_type=FittingCorrection.CorrectionType.CARGO,
                )
            )

    logger.debug(corrections)
    FittingCorrection.objects.bulk_create(corrections)
