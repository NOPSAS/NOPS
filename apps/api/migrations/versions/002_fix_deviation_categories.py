"""Fix deviation_category enum to match domain spec.

Revision ID: 002
Revises: 001
Create Date: 2026-03-14
"""
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None

OLD_VALUES = ["AREA_DEVIATION", "ROOM_COUNT", "ROOM_TYPE", "FLOOR_PLAN",
              "FACADE", "HEIGHT", "SETBACK", "ACCESSIBILITY", "FIRE_SAFETY", "ENERGY"]
NEW_VALUES = ["ROOM_DEFINITION_CHANGE", "BEDROOM_UTILITY_DISCREPANCY",
              "DOOR_PLACEMENT_CHANGE", "WINDOW_PLACEMENT_CHANGE",
              "BALCONY_TERRACE_DISCREPANCY", "ADDITION_DETECTED",
              "UNDERBUILDING_DETECTED", "UNINSPECTED_AREA",
              "USE_CHANGE_INDICATION", "MARKETED_FUNCTION_DISCREPANCY"]

def upgrade() -> None:
    # Delete existing deviations using old categories (dev data only)
    op.execute("DELETE FROM rule_matches")
    op.execute("DELETE FROM deviations")
    # Drop old enum, create new one
    op.execute("ALTER TYPE deviation_category RENAME TO deviation_category_old")
    new_enum_values = ", ".join(f"'{v}'" for v in NEW_VALUES)
    op.execute(f"CREATE TYPE deviation_category AS ENUM ({new_enum_values})")
    op.execute("""
        ALTER TABLE deviations
        ALTER COLUMN category TYPE deviation_category
        USING category::text::deviation_category
    """)
    op.execute("DROP TYPE deviation_category_old")

def downgrade() -> None:
    op.execute("DELETE FROM rule_matches")
    op.execute("DELETE FROM deviations")
    op.execute("ALTER TYPE deviation_category RENAME TO deviation_category_old")
    old_enum_values = ", ".join(f"'{v}'" for v in OLD_VALUES)
    op.execute(f"CREATE TYPE deviation_category AS ENUM ({old_enum_values})")
    op.execute("""
        ALTER TABLE deviations
        ALTER COLUMN category TYPE deviation_category
        USING category::text::deviation_category
    """)
    op.execute("DROP TYPE deviation_category_old")
