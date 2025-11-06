# -*- coding: utf-8 -*-
from alembic import context
import traceback
import transaction

from caerp.alembic.exceptions import MigrationError, RollbackError
from caerp.models.base import DBSESSION, DBBASE


def run_migrations_online():
    from caerp_payment.models import CaerpPaymentHistory
    from caerp_payment.database import ModelBase

    bind = DBSESSION.get_bind(CaerpPaymentHistory)
    if bind is None:
        raise ValueError(
            "\nYou must do CAErp migrations using the 'caerp-migrate' script"
            "\nand not through 'alembic' directly."
        )

    transaction.begin()
    connection = DBSESSION.connection(mapper=CaerpPaymentHistory)

    context.configure(
        connection=connection,
        target_metadata=ModelBase.metadata,
        compare_type=True,
    )

    try:
        context.run_migrations()
    except Exception as migration_e:
        traceback.print_exc()
        try:
            transaction.abort()
        except Exception as rollback_e:
            traceback.print_exc()
            raise RollbackError(rollback_e)
        else:
            raise MigrationError(migration_e)
    else:
        transaction.commit()
    finally:
        # connection.close()
        pass


run_migrations_online()
