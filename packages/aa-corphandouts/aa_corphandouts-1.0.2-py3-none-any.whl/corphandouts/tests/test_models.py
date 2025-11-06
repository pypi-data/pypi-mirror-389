from ..models import DoctrineReport, FittingReport
from .utils import CorphandoutsTestCase
from .utils.fitting import create_sabre_fitting


class TestTasks(CorphandoutsTestCase):

    def test_create_basic_report(self):
        fitting = create_sabre_fitting()

        doctrine_report = DoctrineReport.objects.create(
            name="Test doctrine",
            corporation=self.corporation_audit,
            location_id=self.location.location_id,
            corporation_hangar_division=1,
        )

        FittingReport.objects.create(
            doctrine=doctrine_report,
            fit=fitting,
        )
