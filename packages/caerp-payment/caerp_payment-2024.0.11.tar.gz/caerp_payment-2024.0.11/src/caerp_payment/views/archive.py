"""
Panel associated to the FileArchiveService
"""
import logging
import io
import csv
from caerp.export.utils import write_file_to_request

from caerp_payment.archive import FileArchiveService
from caerp_payment.models import CaerpPaymentArchiveSeal
from .routes import CAERP_PAYMENT_ARCHIVE_ITEM


TYPE_LABELS = {
    "local": "Locale",
    "edocgroup": "Distante (Edoc Group)",
}

logger = logging.getLogger(__name__)


def split_archive_on_history_id(filepath, history_id):
    """
    Renvoie le contenu d'un fichier d'archive jusqu'à la ligne contenant
    l'entrée de journal history_id

    :rtype: io.BytesIO instance
    """
    lines = []
    with open(filepath, "r") as fbuf:
        reader = csv.reader(fbuf)
        for line in reader:
            lines.append(line)
            if line[0] == str(history_id):
                break

    str_result = io.StringIO()
    writer = csv.writer(str_result)
    writer.writerows(lines)
    result = io.BytesIO(str_result.getvalue().encode("utf-8"))
    return result


def archive_file_view(request):
    """
    Stream an archive file content associated to a given archive_seal
    """
    seal_id = request.matchdict["id"]
    archive_seal = (
        request.dbsession.query(CaerpPaymentArchiveSeal).filter_by(id=seal_id).one()
    )

    archive_service = FileArchiveService(None, request)
    filepath = archive_service.get_seal_filepath(archive_seal)
    data_buffer = split_archive_on_history_id(
        filepath, archive_seal.endi_payment_history_id
    )
    write_file_to_request(
        request,
        "{}.csv".format(archive_seal.remote_identification_key),
        data_buffer,
        "text/csv",
    )
    return request.response


def local_file_archive_panel(context, request):
    """
    Collect datas to display local archive informations

    :rtype: dict
    """
    logger.debug("Archive panel")
    archive_seal = (
        request.dbsession.query(CaerpPaymentArchiveSeal)
        .filter_by(endi_payment_history_id=context.id)
        .first()
    )

    result = {
        "archive_seal": archive_seal,
    }

    if archive_seal:
        result["archive_type_label"] = TYPE_LABELS.get(
            archive_seal.archive_type,
            archive_seal.archive_type,
        )
        archive_service = FileArchiveService(context, request)
        result["filename"] = archive_service.filename

        if archive_seal.archive_type == "local":
            result["file_link"] = request.route_path(
                CAERP_PAYMENT_ARCHIVE_ITEM, id=archive_seal.id
            )
        else:
            async_service = archive_service.async_archive_service
            if async_service:
                result["panels"] = async_service.get_ui_plugins()

    logger.debug(result)
    return result


def local_file_archive_list_item_panel(context, request):
    """
    Collect data to display archive related informations in the history list

    :rtype: dict
    """
    if context:
        result = {
            "archive_seal": context,
            "archive_type_label": TYPE_LABELS.get(
                context.archive_type, context.archive_type
            ),
        }
    else:
        result = {}

    return result


def includeme(config):
    config.add_view(
        archive_file_view,
        route_name=CAERP_PAYMENT_ARCHIVE_ITEM,
        permission="admin_treasury",
    )

    config.add_panel(
        local_file_archive_panel,
        "caerp_payment.local_archive_panel",
        renderer="caerp_payment:views/templates/local_archive_panel.mako",
    )
    config.add_panel(
        local_file_archive_list_item_panel,
        "caerp_payment.local_file_archive_list_item_panel",
        renderer="caerp_payment:views/templates/\
local_archive_list_item_panel.mako",
    )
