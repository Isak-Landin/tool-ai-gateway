# db

The `db/` package owns database session management and ORM model definitions.

## Contents

- `db/models.py` — SQLAlchemy ORM model definitions (Project, Message, File)
- `db/session.py` — DB session factory (`SessionLocal`)

## Ownership

- Defines the schema-level row shapes
- Does not own business logic or persistence behavior
- Consumed by all persistence repositories
