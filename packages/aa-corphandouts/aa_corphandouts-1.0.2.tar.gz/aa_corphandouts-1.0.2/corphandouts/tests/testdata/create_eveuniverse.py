from django.test import TestCase
from eveuniverse.tools.testdata import ModelSpec, create_testdata

from . import test_data_filename


class CreateEveUniverseTestData(TestCase):
    def test_create_testdata(self):
        moon_goo_id_range = [i for i in range(16633, 16654)]
        moon_goo_id_range.remove(16645)  # why does this one not exists? #CCPLZ
        testdata_spec = [
            ModelSpec(
                "EveType",
                ids=[
                    22456,  # Sabre
                    2873,  # 125mm AC II
                    22782,  # Sphere launcher
                    20565,  # Cloak
                    8517,  # Compact MSE
                    35658,  # 5MN
                    40758,  # Scram II
                    2605,  # Nanos II
                    31165,  # Small hyper II
                    12608,  # Hail S
                    12625,  # Barrage S
                    22778,  # Bubble
                ],
            )
        ]
        create_testdata(testdata_spec, test_data_filename())
