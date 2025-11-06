from corptools.models import CorporationAudit, EveLocation

from django.test import TestCase

from allianceauth.eveonline.models import EveCorporationInfo

from corphandouts.models import DoctrineReport, FittingReport

from ..testdata.load_eveuniverse import load_eveuniverse
from .fitting import create_sabre_fitting

LOCATION_ID = 1


class CorphandoutsTestCase(TestCase):
    """Test case preloading the data needed for this app"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        location, corporation_audit = preload_corptools_data()
        cls.location = location
        cls.corporation_audit = corporation_audit
        load_eveuniverse()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.location.delete()
        cls.corporation_audit.delete()


def preload_corptools_data() -> tuple[EveLocation, CorporationAudit]:
    """Basic preload function"""
    location = EveLocation.objects.create(
        location_id=LOCATION_ID, location_name="TestStationLocation"
    )
    corp = EveCorporationInfo.objects.get_or_create(
        corporation_id=123,
        corporation_name="corporation.name1",
        corporation_ticker="ABC",
        member_count=1,
        ceo_id=1,
    )[0]
    corpaudit = CorporationAudit.objects.create(corporation=corp)

    return location, corpaudit


def create_basic_doctrine_report(
    corporation_audit: CorporationAudit, location: EveLocation
) -> DoctrineReport:
    """Creates a simple doctrine report"""
    saved_fitting = create_sabre_fitting()

    doctrine_report = DoctrineReport.objects.create(
        name="Test doctrine",
        corporation=corporation_audit,
        location_id=location.location_id,
        corporation_hangar_division=1,
    )

    FittingReport.objects.create(
        doctrine=doctrine_report,
        fit=saved_fitting,
    )

    return doctrine_report
