# -*- coding: utf-8 -*-
"""
Payment History service, records modification done on payments
"""
import logging
from sqlalchemy import desc
from caerp_payment.interfaces import IPaymentArchiveService
from caerp_payment.models import CaerpPaymentHistory


class HistoryLogService(object):
    """
    History service that's only logging the actions in a log file.

    To be used in dev mode
    """

    def __init__(self, context, request):
        self.request = request
        self.logger = logging.getLogger("caerp_payment")
        self.archive_service = request.find_service(IPaymentArchiveService)
        self.dbsession = request.dbsession

    def record(self, action, invoice, payment):
        self.logger.debug("Recording an action")
        self.logger.debug("Action : %s" % action)
        self.logger.debug("User : %s" % self.request.identity)
        self.logger.debug("Invoice id : %s" % invoice.id)


class HistoryDBService(HistoryLogService):
    """
    Service logging datas in a database using a specific connexion
    """

    def get_previous_entry_hash(self):
        """
        Produce a hash of the csv representation of the previous history entry

        :param obj dbsession: The current database session
        :rtype: str
        """
        previous_entry = (
            self.dbsession.query(CaerpPaymentHistory)
            .order_by(desc(CaerpPaymentHistory.created_at))
            .first()
        )

        if previous_entry:
            result = previous_entry.get_hash()
        else:
            result = ""
        print(result)
        return result

    def record(self, action, invoice, payment):
        """
        Record an action on a payment

        1- Record the action
        2- If an archive service exists, creates an archive

        :param str action: The type of action
        :param obj invoice: The related Invoice instance
        :param obj payment: The related payment object
        """
        self.logger.info("Recording an action")
        self.logger.info("Action : %s" % action)
        self.logger.info("User : %s" % self.request.identity)
        self.logger.info("Invoice id : %s" % invoice.id)
        self.logger.info("It's production mode")

        previous_entry_hash = self.get_previous_entry_hash()
        record = CaerpPaymentHistory(
            action_type=action,
            payment_id=payment.id,
            mode=payment.mode,
            amount=payment.amount,
            bank_remittance_id=payment.bank_remittance_id,
            date=payment.date,
            invoice_id=invoice.id,
            invoice_pdf_file_hash=invoice.pdf_file_hash,
            bank_cg=payment.bank.compte_cg,
            tva_value=payment.tva.value,
            user_login=self.request.identity.login.login,
            previous_entry_hash=previous_entry_hash,
        )
        self.dbsession.add(record)
        self.dbsession.flush()
        self.archive_service.archive(record)
        self.logger.info("Recorded")
