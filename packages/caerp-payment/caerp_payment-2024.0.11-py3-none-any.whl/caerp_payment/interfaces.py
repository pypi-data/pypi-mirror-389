# -*- coding: utf-8 -*-
from zope.interface import Interface, Attribute


class IPaymentRecordHistoryService(Interface):
    """
    History manipulation tool iinterface for Payment action log
    """

    def record_action(self, action, invoice, payment):
        """
        History manipulation tool for Payment registration
        """
        pass


class IPaymentArchiveService(Interface):
    """
    Archive service is used to archive payment datas and secure its content
    integrity with the help of third-party services
    """

    def archive(self, history):
        """
        Stores a single history item

        :param obj history: A CaerpPaymentHistory instance
        :rtype: class:`caerp_payment.models.CaerpPaymentArchiveSeal
        """
        pass

    def is_archived(self, history):
        """
        Check if the given history item has been archived remotely

        :param obj history: A CaerpPaymentHistory instance
        :rtype: bool
        """
        pass

    def find(self, history):
        """
        Find A CaerpPaymentArchiveSeal that matches the given history

        :param obj history: A CaerpPaymentHistory instance
        :rtype: class:`caerp_payment.models.CaerpPaymentArchiveSeal
        """

    def get_ui_plugins(self):
        """
        List ui panels that should be used in display

        See pyramid_layout to known what a panel is

        :returns: List of panel names
        :rtype: list
        """

    def get_ui_list_plugin(self):
        """
        Collect the ui panel used to display archive informations

        :returns: The name of a panel
        :rtype: str
        """

    def stream_list_actions(self, history):
        """
        Stream actions available in the history list view

        :returns: List all the available actions
        :rtype: list
        """


class IPaymentAsyncArchiveService(Interface):
    """
    Asynchronous archive service that will remotely backup a given archive file

    This Service is supposed to produce a certification along the file that
    will be uploaded

    The file related information can be stored with the CaerpPaymentArchiveSeal
    model
    """

    # Key used in database
    archive_type_key = Attribute("""key used in the database""")

    def archive(self, history, filename, filecontent):
        """
        Archive the given file buffer's content

        :param obj history: A CaerpPaymentHistory instance
        :param str filename: The name of the archived file
        :param str filecontent: A read buffer of the content to archive
        :returns: True/False if the async task is launched
        :rtype: bool
        """
        pass

    def get_ui_plugins(self):
        """
        List ui panels that should be used in display

        See pyramid_layout to known what a panel is

        :returns: List of panel names
        :rtype: list
        """

    def stream_list_actions(self, history):
        """
        Stream actions available in the history list view

        :returns: List all the available actions
        :rtype: list
        """
