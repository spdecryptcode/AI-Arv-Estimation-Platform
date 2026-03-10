"""initial properties table

Revision ID: 0001_create_properties_table
Revises: 
Create Date: 2026-02-27 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

# revision identifiers, used by Alembic.
revision = '0001_create_properties_table'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'properties',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('address', sa.String(), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )


def downgrade():
    op.drop_table('properties')
