from corptools.models import EveItemType

from ..corptools import get_ship_fit
from ..models import FittingCorrection, FittingToCorrect
from ..tasks import update_all_doctrine_reports
from .utils import CorphandoutsTestCase, create_basic_doctrine_report
from .utils.corptools import corptools_create_fitted_sabre, corptools_create_sabre_stack


class TestTasks(CorphandoutsTestCase):

    def test_update_doctrine_report_no_errors(self):
        create_basic_doctrine_report(self.corporation_audit, self.location)
        corptools_create_fitted_sabre(self.location, self.corporation_audit)

        update_all_doctrine_reports()

        self.assertEqual(0, FittingCorrection.objects.count())

    def test_update_doctrine_report_fitting_error(self):
        create_basic_doctrine_report(self.corporation_audit, self.location)
        sabre = corptools_create_fitted_sabre(self.location, self.corporation_audit)
        sabre_fitting = get_ship_fit(sabre.item_id)

        slot_0_125mm = sabre_fitting.get(location_flag="HiSlot0", type_id=2873)
        slot_0_125mm.type_id = 484
        slot_0_125mm.type_name = EveItemType.objects.get_or_create_from_esi(484)[0]
        slot_0_125mm.save()

        update_all_doctrine_reports()

        self.assertEqual(2, FittingCorrection.objects.count())

    def test_ships_are_deleted_on_updates(self):
        doctrine_report = create_basic_doctrine_report(
            self.corporation_audit, self.location
        )
        fitting_report = doctrine_report.fittings.all()[0]
        FittingToCorrect.objects.create(
            item_name="Test to delete",
            item_id=1,
            fit=fitting_report,
        )

        update_all_doctrine_reports()

        self.assertEqual(
            0,
            FittingToCorrect.objects.filter(
                item_name="Test to delete", item_id=1
            ).count(),
        )

    def test_no_error_if_ship_stack(self):
        """The task shouldn't include ship stacks when trying to find ships to update"""
        create_basic_doctrine_report(self.corporation_audit, self.location)
        corptools_create_sabre_stack(self.location, self.corporation_audit)

        update_all_doctrine_reports()

        self.assertEqual(0, FittingToCorrect.objects.count())
