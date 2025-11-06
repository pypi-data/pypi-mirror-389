def includeme(config):
    settings = config.get_settings()
    key = "caerp_payment.interfaces.IPaymentRecordHistoryService"
    if key in settings and settings[key] == "caerp_payment.history.HistoryDBService":
        config.include(".history")

    key = "caerp_payment.interfaces.IPaymentArchiveService"
    if key in settings and settings[key] == "caerp_payment.archive.FileArchiveService":
        config.include(".archive")
