"""
Code related to generating multibuy to be imported into eve
"""

from eveuniverse.models import EveType


def generate_multibuy(type_list: list[tuple[EveType, int]]) -> str:
    """
    Generates a multibuy from a list of tuples with (EveType, count)

    Armor Reinforcement Charge	2
    Rapid Repair Charge	1
    """

    return "\n".join(f"{eve_type.name}\t{count}" for eve_type, count in type_list)
