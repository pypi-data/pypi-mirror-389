"""Admin site."""

from corptools.models import CorpAsset, EveLocation

from django import forms
from django.contrib import admin
from django.db.models import QuerySet

from corphandouts.models import DoctrineReport, FittingReport
from corphandouts.tasks import update_doctrine_report


@admin.action(description="Updates the selected doctrine reports")
def update_doctrine(modeladmin, request, queryset: QuerySet[DoctrineReport]):
    for doctrine_report in queryset:
        update_doctrine_report.delay(doctrine_report.id)


class DoctrineReportForm(forms.ModelForm):
    class Meta:
        model = DoctrineReport
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        asset_locations_names_queryset = (
            CorpAsset.objects.filter(location_name__isnull=False)
            .values_list("location_name")
            .distinct()
        )
        asset_locations_queryset = EveLocation.objects.filter(
            location_id__in=asset_locations_names_queryset, managed=False
        ).order_by("location_name")
        # TODO filter out metenoxes
        self.fields["location"].queryset = asset_locations_queryset


class FitInline(admin.TabularInline):
    model = FittingReport
    readonly_fields = ["ok_ships"]


@admin.register(DoctrineReport)
class DoctrineReportAdmin(admin.ModelAdmin):
    form = DoctrineReportForm
    inlines = (FitInline,)
    actions = [update_doctrine]
