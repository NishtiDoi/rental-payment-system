from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.database import Base
from app.models import (
    user,
    bank_account,
    property,
    lease,
    transaction,
    transaction_event,
    payment_schedule,
    audit_log,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
