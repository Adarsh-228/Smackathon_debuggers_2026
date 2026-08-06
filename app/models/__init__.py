# Import all models here so that Base has them before Alembic imports Base
from app.core.database import Base
from app.models.collaboration import *
from app.models.document import *
from app.models.reconciliation import *
from app.models.workflow import *
