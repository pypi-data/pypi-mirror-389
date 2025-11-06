"""Models."""

from corptools.models import CorporationAudit, EveLocation
from fittings.models import Fitting

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from eveuniverse.models import EveType

from corphandouts.multibuy import generate_multibuy


class General(models.Model):
    """A metamodel for app permissions."""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("basic_access", "Can access this app and view corporation handouts"),
            ("manager", "Can view handouts for all corporations"),
        )


class DoctrineReport(models.Model):
    """Defines a group of fittings to be linked together in reports"""

    name = models.CharField(max_length=50, help_text=_("Doctrine name"))
    corporation = models.ForeignKey(
        CorporationAudit,
        on_delete=models.CASCADE,
        help_text=_("Corporation to get the assets from"),
    )
    location = models.ForeignKey(
        EveLocation,
        on_delete=models.CASCADE,
        help_text=_("Where the doctrine should be located"),
    )
    corporation_hangar_division = models.IntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(7)]
    )

    def __str__(self):
        return f"{self.name} / {self.corporation.corporation.corporation_name} / {self.location.location_name}"

    @property
    def first_ship_type_id(self) -> int:
        """Returns the type if of the first ship in the ship list"""
        fittings = self.fittings.all()
        if fittings.exists():
            return fittings[0].fit.ship_type_type_id
        return 0

    @property
    def ship_types_ids(self) -> list[int]:
        """Return all ship type ids in the doctrine"""
        return self.fittings.values_list("fit__ship_type__id", flat=True)

    @property
    def count_corrections(self) -> int:
        """Return the number of fits to correct known for this corporation"""
        return self.fittings.values("fit_to_correct").count()

    def count_missing(self) -> int | None:
        """Returns how many fits are missing"""
        return sum(
            fitting_report.count_missing()
            for fitting_report in self.fittings.all()
            if fitting_report.count_missing()
        )

    def get_multibuy_string(self) -> str:
        """Generates a multibuy string with all missing types"""
        postitive_corrections = FittingCorrection.objects.filter(
            fit_to_correct__fit__doctrine=self,
            correction__gt=0,
        )  # return corrections that need stuffs bought
        correction_list = [
            (correction.eve_type, correction.correction)
            for correction in postitive_corrections
        ]

        multibuy_str = generate_multibuy(correction_list)

        return multibuy_str


class FittingReport(models.Model):
    """Defines how a fit should be found in the corporation hangars"""

    doctrine = models.ForeignKey(
        DoctrineReport, on_delete=models.CASCADE, related_name="fittings"
    )
    fit = models.ForeignKey(Fitting, on_delete=models.CASCADE)
    expected_amount = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_(
            "Amount of fits expected in the corp hangar. Set to 0 to ignore this fit"
        ),
    )
    regex = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        help_text=_("Optional regex to get ships from"),
    )

    ok_ships = models.PositiveIntegerField(
        default=0, help_text=_("Current amount of ships fitted correctly")
    )

    @property
    def count_errors(self) -> int:
        """Return the number of fits to fix"""
        return self.fits_to_correct.count()

    def count_missing(self) -> int:
        """
        If there's an expected amount returns how many should be added to meet this amount
        Ships to refit are not considered missing
        """
        if self.expected_amount and self.expected_amount > self.ok_ships:
            return self.expected_amount - (self.ok_ships + self.count_errors)
        return 0

    def get_multibuy_string(self) -> str:
        """Generates a multibuy string with all missing types"""
        postitive_corrections = FittingCorrection.objects.filter(
            fit_to_correct__fit=self,
            correction__gt=0,
        )  # return corrections that need stuffs bought
        correction_list = [
            (correction.eve_type, correction.correction)
            for correction in postitive_corrections
        ]

        multibuy_str = generate_multibuy(correction_list)

        return multibuy_str

    def __str__(self):
        return f"{self.fit} {self.doctrine.name}"


class FittingToCorrect(models.Model):
    """
    Represents a fit that needs to be fixed
    """

    item_name = models.CharField(max_length=40, help_text=_("Name of the ship"))
    item_id = models.BigIntegerField(help_text=_("Item id if the ship§"))
    fit = models.ForeignKey(
        FittingReport,
        on_delete=models.CASCADE,
        related_name="fits_to_correct",
        related_query_name="fit_to_correct",
    )

    def __str__(self):
        return f"{self.fit.fit.ship_type.name} / {self.item_name}"

    @property
    def id(self):
        """Return primary key id"""
        return self.item_id

    def get_correction_icons(self) -> list[tuple[int, str]]:
        """Return a list of type ids for icons representing the categories that need corrections"""
        icon_type_ids = []
        if self._category_has_error("Charge"):
            icon_type_ids.append(
                (230, _("This fitting is missing charges"))
            )  # Antimatter M
        if self._category_has_error("Module"):
            icon_type_ids.append(
                (496, _("This fit is missing modules"))
            )  # 800mm cannon I
        if self._category_has_error("Implant"):
            icon_type_ids.append(
                (28680, _("This fit is missing implants and/or drugs"))
            )  # Synth mindflood
        return icon_type_ids

    def _category_has_error(self, category_name: str) -> bool:
        """Return true if among the fit corrections one of them is part of the eve category with this name"""
        return self.corrections.filter(
            eve_type__eve_group__eve_category__name=category_name
        ).exists()

    def get_multibuy_string(self) -> str:
        """Generates a multibuy string with all missing types"""
        postitive_corrections = self.corrections.filter(
            correction__gte=0
        )  # return corrections that need stuffs bought
        correction_list = [
            (correction.eve_type, correction.correction)
            for correction in postitive_corrections
        ]

        multibuy_str = generate_multibuy(correction_list)

        return multibuy_str


class FittingCorrection(models.Model):
    """
    Represents a correction to do on a fit
    """

    class CorrectionType(models.TextChoices):
        """Cargo of fitting issue"""

        CARGO = "CA", "Cargo"
        FITTING = "FI", "Fitting"

        @classmethod
        def from_value_to_label(cls, value: str | None) -> str:
            """Return the label from one of the possible values"""
            match value:
                case "CA":
                    return _("Cargo")
                case "FI":
                    return _("Fitting")
                case _:
                    return _("Unknown")

    fit_to_correct = models.ForeignKey(
        FittingToCorrect,
        on_delete=models.CASCADE,
        related_name="corrections",
        related_query_name="correction",
    )
    eve_type = models.ForeignKey(EveType, on_delete=models.CASCADE)
    correction = models.IntegerField(
        help_text=_("Amount to remove/add to the fit to match the template")
    )
    correction_type = models.CharField(max_length=2, choices=CorrectionType.choices)

    def __str__(self):
        return f"({self.fit_to_correct}) / {self.eve_type} / {self.correction}"
