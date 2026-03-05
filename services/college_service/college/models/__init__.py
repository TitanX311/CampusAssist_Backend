from sqlalchemy.orm import declarative_base

Base = declarative_base()

# ensure models are registered when this package is imported
from college.models import college  # noqa: F401
from college.models import community  # noqa: F401
