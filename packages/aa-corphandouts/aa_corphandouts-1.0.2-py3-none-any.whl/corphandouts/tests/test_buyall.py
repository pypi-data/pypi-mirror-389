from eveuniverse.models import EveType

from ..models import FittingCorrection, FittingToCorrect
from ..multibuy import generate_multibuy
from .utils import CorphandoutsTestCase, create_basic_doctrine_report


class TestBuyAll(CorphandoutsTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.HAIL_S = EveType.objects.get(id=12608)
        cls.T2_NANO = EveType.objects.get(id=2605)

        cls.EXPECTED_STR = """Nanofiber Internal Structure II\t2
Hail S\t200"""

    def test_generate(self):
        type_list = [(self.T2_NANO, 2), (self.HAIL_S, 200)]

        self.assertEqual(generate_multibuy(type_list), self.EXPECTED_STR)

    def test_generate_from_fit(self):
        self.setup_classes()
        self.assertEqual(self.fit_to_correct.get_multibuy_string(), self.EXPECTED_STR)

    def test_generate_from_fitting_report(self):
        self.setup_classes()
        self.assertEqual(self.fitting_report.get_multibuy_string(), self.EXPECTED_STR)

    def test_generate_from_doctrine_report(self):
        self.setup_classes()
        self.assertEqual(self.doctrine_report.get_multibuy_string(), self.EXPECTED_STR)

    def setup_classes(self):
        """Util functions created the models to be tested"""
        self.doctrine_report = create_basic_doctrine_report(
            self.corporation_audit, self.location
        )
        self.fitting_report = self.doctrine_report.fittings.all()[0]

        self.fit_to_correct = FittingToCorrect.objects.create(
            item_name="Test fitting correction",
            item_id=1,
            fit=self.fitting_report,
        )
        self.__create_corrections_for_fit(self.fit_to_correct)

    def __create_corrections_for_fit(self, fit_to_correct: FittingToCorrect):
        """Util functions adding corrections to a FitToCorrect"""

        FittingCorrection.objects.create(
            fit_to_correct=fit_to_correct,
            eve_type=self.T2_NANO,
            correction=2,
            correction_type=FittingCorrection.CorrectionType.FITTING,
        )

        FittingCorrection.objects.create(
            fit_to_correct=fit_to_correct,
            eve_type=self.HAIL_S,
            correction=200,
            correction_type=FittingCorrection.CorrectionType.CARGO,
        )
