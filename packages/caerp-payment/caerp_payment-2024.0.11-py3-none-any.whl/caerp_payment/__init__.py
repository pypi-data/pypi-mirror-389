# -*- coding:utf-8 -*-
from pyramid.path import DottedNameResolver

from caerp_payment.interfaces import (
    IPaymentRecordHistoryService,
    IPaymentArchiveService,
)


def configure_history_service(config, settings):
    """
    Configure the history service that will be used to log the Payment history
    """
    module_path = "caerp_payment.history.HistoryLogService"
    key = "caerp_payment.interfaces.IPaymentRecordHistoryService"

    if key in settings:
        module_path = settings[key]

    # si c'est un service de stockage en bdd on doit configurer la session
    # interne au module
    if module_path == "caerp_payment.history.HistoryDBService":
        if "caerp_payment_db.url" not in settings:
            raise Exception(
                "caerp_payment.dev est à false et aucune url "
                "caerp_payment_db.url n'est fourni"
            )
        else:
            # We will store the caerp payment's history
            config.include(".database")

    history_service = DottedNameResolver().resolve(module_path)
    config.register_service_factory(history_service, IPaymentRecordHistoryService)


def configure_archive_service(config, settings):
    """
    Configure the Archive service that will be used to archive the Payment
    history log
    """
    module_path = "caerp_payment.archive.DefaultArchiveService"
    key = "caerp_payment.interfaces.IPaymentArchiveService"

    if key in settings:
        module_path = settings[key]

    service = DottedNameResolver().resolve(module_path)

    if hasattr(service, "check_settings"):
        service.check_settings(settings)

    config.register_service_factory(service, IPaymentArchiveService)


def includeme(config):
    settings = config.get_settings()
    configure_history_service(config, settings)
    configure_archive_service(config, settings)
