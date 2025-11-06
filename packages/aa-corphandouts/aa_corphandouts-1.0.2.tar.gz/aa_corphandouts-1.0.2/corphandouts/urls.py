"""Routes."""

from django.urls import path

from . import views

app_name = "corphandouts"

urlpatterns = [
    path("", views.index, name="index"),
    path(
        "doctrine/<int:doctrine_id>",
        views.doctrine_fitting_reports,
        name="doctrine_report",
    ),
    path(
        "doctrine/<int:doctrine_id>/fits",
        views.doctrine_fit_reports_all,
        name="doctrine_fit_report_all",
    ),
    path(
        "doctrine/<int:doctrine_id>/fits/<int:fitting_report_id>",
        views.fitting_reports,
        name="doctrine_fit_report",
    ),
    path("fitting/<int:fitting_id>", views.fitting, name="fitting"),
    path("modal_loader_body", views.modal_loader_body, name="modal_loader_body"),
]
