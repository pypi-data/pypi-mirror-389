from corphandouts.corptools import get_assets_corporation_division, get_ship_fit

from .utils import CorphandoutsTestCase
from .utils.corptools import corptools_create_fitted_sabre


class CorptoolsTest(CorphandoutsTestCase):

    def test_get_assets_corporation_division(self):
        sabre_asset = corptools_create_fitted_sabre(
            self.location, self.corporation_audit
        )

        assets_in_corp_division = get_assets_corporation_division(
            self.corporation_audit, self.location, 1
        )

        self.assertIn(sabre_asset, assets_in_corp_division)
        self.assertEqual(1, assets_in_corp_division.count())

    def test_get_ship_fit(self):
        sabre_asset = corptools_create_fitted_sabre(
            self.location, self.corporation_audit
        )

        sabre_fit = get_ship_fit(sabre_asset.item_id)

        self.assertEqual(18, sabre_fit.count())
        self.assertEqual(
            8, sabre_fit.filter(location_flag__regex=r"^HiSlot\d$").count()
        )
        self.assertEqual(
            4, sabre_fit.filter(location_flag__regex=r"^MedSlot\d$").count()
        )
        self.assertEqual(
            2, sabre_fit.filter(location_flag__regex=r"^LoSlot\d$").count()
        )
        self.assertEqual(
            2, sabre_fit.filter(location_flag__regex=r"^RigSlot\d$").count()
        )
        self.assertEqual(2000, sabre_fit.get(type_id=12608).quantity)
        self.assertEqual(1000, sabre_fit.get(type_id=12625).quantity)
