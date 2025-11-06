"""Views."""

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import cache_page

from allianceauth.services.hooks import get_extension_logger

from corphandouts.models import DoctrineReport, FittingReport, FittingToCorrect

logger = get_extension_logger(__name__)


def add_common_context(context: dict = None) -> dict:
    """Enhance the templates context with context that should be added to every page"""
    if context is None:
        context = {}

    if basic_title := context.get("page_title"):
        context["page_title"] = f"{basic_title} - Corporation Handouts"
    else:
        context["page_title"] = "Corporation Handouts"

    return context


@login_required
@permission_required("corphandouts.basic_access")
def index(request):
    """Render index view."""
    doctrines = DoctrineReport.objects.all()
    return render(
        request,
        "corphandouts/index.html",
        add_common_context(
            {
                "doctrines": doctrines,
            }
        ),
    )


@login_required
@permission_required("corphandouts.basic_access")
def doctrine_fitting_reports(request, doctrine_id: int):
    """Shows all fitting reports for this doctrine"""
    logger.info("Trying to show fitting reports for doctrine id %d", doctrine_id)
    doctrine_report = get_object_or_404(DoctrineReport, pk=doctrine_id)

    fitting_reports_list = doctrine_report.fittings.all()
    logger.debug(fitting_reports_list)

    return render(
        request,
        "corphandouts/doctrine.html",
        add_common_context(
            {
                "doctrine_report": doctrine_report,
                "fitting_reports": fitting_reports_list,
            }
        ),
    )


@login_required
@permission_required("corphandouts.basic_access")
def doctrine_fit_reports_all(request, doctrine_id: int):
    """Shows all fittings with errors for this doctrine"""
    logger.info("Trying to show all fitting errors for doctrine id %d", doctrine_id)
    doctrine_report = get_object_or_404(DoctrineReport, pk=doctrine_id)
    logger.debug(doctrine_report)

    fittings = []
    for fitting_report in doctrine_report.fittings.all():
        fittings.extend(fitting_report.fits_to_correct.all())
    logger.debug(fittings)

    return render(
        request,
        "corphandouts/fittings.html",
        add_common_context({"doctrine_id": doctrine_id, "fittings": fittings}),
    )


@login_required
@permission_required("corphandouts.basic_access")
def fitting_reports(request, doctrine_id: int, fitting_report_id: int):
    """Doctrine report view for a single fit"""
    fitting_report_list = get_object_or_404(
        FittingReport, doctrine_id=doctrine_id, pk=fitting_report_id
    )
    logger.info(fitting_report_list)

    fittings = fitting_report_list.fits_to_correct.all()
    logger.debug(fittings)

    return render(
        request,
        "corphandouts/fittings.html",
        add_common_context(
            {"doctrine_id": doctrine_id, "fittings": fittings},
        ),
    )


@login_required
@permission_required("corphandouts.basic_access")
def fitting(request, fitting_id: int):
    """Fitting report"""
    fitting_to_correct = get_object_or_404(FittingToCorrect, pk=fitting_id)

    context = {
        "fitting": fitting_to_correct,
    }

    logger.info(fitting_id)

    if request.GET.get("new_page"):
        context["title"] = "title"
        context["content_file"] = "corphandouts/partials/fit_corrections.html"
        return render(
            request,
            "corphandouts/modals/generic_modal_page.html",
            add_common_context(context),
        )
    return render(
        request, "corphandouts/modals/fit_corrections.html", add_common_context(context)
    )


@cache_page(3600)
def modal_loader_body(request):
    """Draw the loader body. Useful for showing a spinner while loading a modal."""
    return render(request, "corphandouts/modals/loader_body.html")
