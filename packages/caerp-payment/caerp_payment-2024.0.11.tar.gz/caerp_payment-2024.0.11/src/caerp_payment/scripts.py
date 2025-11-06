# -*-coding:utf-8-*-
import datetime
import logging
import os
import random

from caerp.scripts.utils import command


def generate_archives_command(arguments, env):
    """
    Generate archive files based on payment database entries
    """
    logger = logging.getLogger(__name__)
    logger.debug("Generating archive files")
    from caerp.models.base.base import DBSESSION
    from zope.sqlalchemy import mark_changed

    from caerp_payment.archive import FileArchiveService
    from caerp_payment.models import CaerpPaymentArchiveSeal, CaerpPaymentHistory

    storage = env["request"].registry.settings[FileArchiveService.settings_key]
    logger.debug("  + Working with directory {}".format(storage))
    os.system("rm -f {}/*.csv".format(storage))

    dbsession = DBSESSION()
    seals = dbsession.query(CaerpPaymentArchiveSeal).all()
    logger.debug(" Deleting {} seals".format(len(seals)))
    for seal in seals:
        dbsession.delete(seal)

    entries = (
        dbsession.query(CaerpPaymentHistory)
        .order_by(CaerpPaymentHistory.created_at)
        .all()
    )

    logger.debug(" + {} entries".format(len(entries)))
    for index, entry in enumerate(entries):
        if index > 0:
            entry.previous_entry_hash = entries[index - 1].get_hash()
        else:
            entry.previous_entry_hash = ""
        archive_service = FileArchiveService(None, env["request"])
        archive_service.filename = archive_service.get_filename(entry.created_at)
        archive_service.filepath = os.path.join(
            archive_service.storage_path, archive_service.filename
        )
        seal = archive_service.archive(entry)
        seal.created_at = entry.created_at + datetime.timedelta(
            microseconds=random.randint(100, 350)
        )
    mark_changed(dbsession)


def entry_point():
    """CAErp payment archive generation tool
    Usage:
        caerp-payment <config_uri> gen_archive
    """
    try:
        return command(generate_archives_command, entry_point.__doc__)
    finally:
        pass
