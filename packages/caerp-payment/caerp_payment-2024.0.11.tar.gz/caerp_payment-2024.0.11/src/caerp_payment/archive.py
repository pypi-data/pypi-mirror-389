# -*- coding: utf-8 -*-
"""
Caerp storage services
"""
import datetime
import hashlib
import os
import logging

from caerp_payment.models import CaerpPaymentArchiveSeal
from caerp_payment.interfaces import IPaymentAsyncArchiveService
from caerp.utils.widgets import Link
from caerp_payment.views.routes import CAERP_PAYMENT_ARCHIVE_ITEM


class DefaultArchiveService(object):
    ui_panel_name = "caerp_payment.local_archive_panel"
    ui_list_item_panel_name = "caerp_payment.local_file_archive_list_item_panel"

    def __init__(self, context, request):
        self.request = request
        self.logger = logging.getLogger("caerp_payment")
        self.dbsession = request.dbsession

    def archive(self, history):
        self.logger.debug("Archiving history item {}".format(history.id))
        id_key = "No persistent archive system has been used"
        result = CaerpPaymentArchiveSeal(
            remote_identification_key=id_key, endi_payment_history_id=history.id
        )
        return result

    def is_archived(self, history):
        return False

    def find(self, history):
        """
        Find A CaerpPaymentArchiveSeal that matches the given history

        :param obj history: A CaerpPaymentHistory instance
        :rtype: class:`caerp_payment.models.CaerpPaymentArchiveSeal
        """
        query = self.dbsession.query(CaerpPaymentArchiveSeal)
        query = query.filter(
            CaerpPaymentArchiveSeal.endi_payment_history_id == history.id
        )
        return query.first()

    def get_ui_plugins(self):
        """
        List the panels to use in the history view
        """
        return [self.ui_panel_name]

    def get_ui_list_plugin(self):
        """
        List the panels to use in the history view
        """
        return self.ui_list_item_panel_name

    def stream_list_actions(self, seal):
        if seal:
            yield Link(
                self.request.route_path(CAERP_PAYMENT_ARCHIVE_ITEM, id=seal.id),
                "Télécharger l'archive",
                title="Voir le détail de cette entrée",
                icon="archive",
            )


class FileArchiveService(object):
    """
    FileStorageService simply logs the history in a file
    """

    settings_key = "caerp_payment_archive_storage_path"
    ui_panel_name = "caerp_payment.local_archive_panel"
    ui_list_item_panel_name = "caerp_payment.local_file_archive_list_item_panel"

    def __init__(self, context, request):
        self.logger = logging.getLogger("caerp_payment")
        self.request = request
        self.dbsession = request.dbsession
        self.storage_path = self.request.registry.settings[self.settings_key]
        self.filename = self.get_filename()
        self.filepath = os.path.join(self.storage_path, self.filename)

        try:
            self.async_archive_service = request.find_service(
                IPaymentAsyncArchiveService
            )
        except:
            self.logger.exception("No async archive service was configured")
            self.async_archive_service = None

    def get_filename(self, date=None):
        if date is None:
            date = datetime.date.today()
        return "payment_storage_{}_{}.csv".format(date.year, date.month)

    def get_seal_filepath(self, archive_seal):
        """
        Return the path to the file associated to the given archive_seal

        :param obj archive_seal: The CaerpPaymentArchiveSeal instance
        :rtype: str
        """
        filename = self.get_filename(date=archive_seal.created_at)
        return os.path.join(self.storage_path, filename)

    def _get_archive_filecontent(self):
        return open(self.filepath, "rb").read()

    def _get_id_key(self, filecontent):
        id_key = hashlib.sha1(filecontent).hexdigest()
        return id_key

    def archive(self, history):
        """
        Archive the given history entry

        :returns: A Sha1 sum of the output file content
        :rtype: str
        """
        with open(self.filepath, "a") as fbuf:
            fbuf.write(history.serialize())

        filecontent = self._get_archive_filecontent()

        if self.async_archive_service is not None:
            self.async_archive_service.archive(history, self.filename, filecontent)
            # The seal will be produced asynchronously
            result = None
            self.logger.debug("No archive seal was produced locally")
            self.logger.debug("The asynchronous service should handle this")
        else:
            # The seal is produced locally
            id_key = self._get_id_key(filecontent)
            result = CaerpPaymentArchiveSeal(
                archive_type="local",
                remote_identification_key=id_key,
                endi_payment_history_id=history.id,
            )
            self.dbsession.add(result)
            self.dbsession.flush()
        return result

    def is_archived(self, history):
        """
        Check if the payment history entry has been archived

        :param obj history: The CaerpPaymentHistory instance
        :rtype: bool
        """
        query = self.dbsession.query(CaerpPaymentArchiveSeal.id)
        query = query.filter(
            CaerpPaymentArchiveSeal.endi_payment_history_id == history.id
        )
        result = query.count() > 0
        return result

    def find(self, history):
        """
        Find A CaerpPaymentArchiveSeal that matches the given history

        :param obj history: A CaerpPaymentHistory instance
        :rtype: class:`caerp_payment.models.CaerpPaymentArchiveSeal
        """
        query = self.dbsession.query(CaerpPaymentArchiveSeal)
        query = query.filter(
            CaerpPaymentArchiveSeal.endi_payment_history_id == history.id
        )
        return query.first()

    def get_ui_plugins(self):
        """
        List the panels to use in the history view
        """
        return [self.ui_panel_name]

    def get_ui_list_plugin(self):
        """
        List the panels to use in the history view
        """
        return self.ui_list_item_panel_name

    def stream_list_actions(self, seal):
        if seal:
            if seal.archive_type == "local":
                yield Link(
                    self.request.route_path(CAERP_PAYMENT_ARCHIVE_ITEM, id=seal.id),
                    "Télécharger l'archive",
                    title="Voir le détail de cette entrée",
                    icon="archive",
                )
            elif (
                self.async_archive_service
                and seal.archive_type == self.async_archive_service.archive_type_key
            ):
                for action in self.async_archive_service.stream_list_actions(seal):
                    yield action

    @classmethod
    def check_settings(cls, settings):
        """
        Check the settings contains the caerp_payment_archive_storage_path if
        this given service is configured in the ini file

        :raises: KeyError if the key is missing
        :raises: Exception if the directory doesn't exist
        """
        if cls.settings_key not in settings:
            raise KeyError(
                "You should configure {} in your .ini file".format(cls.settings_key)
            )

        storage_path = settings[cls.settings_key]
        if not os.path.isdir(storage_path):
            raise Exception("Invalid storage path {}".format(storage_path))
