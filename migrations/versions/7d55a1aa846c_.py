"""empty message

Revision ID: 7d55a1aa846c
Revises: 7b4ddcd424df
Create Date: 2020-04-30 17:58:03.311447

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7d55a1aa846c'
down_revision = '7b4ddcd424df'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Artist', sa.Column('seeking_venue', sa.Boolean(), nullable=True))
    op.add_column('Artist', sa.Column('venue_description', sa.String(length=500), nullable=True))
    op.add_column('Artist', sa.Column('website', sa.String(length=120), nullable=True))
    op.add_column('Venue', sa.Column('seeking_talent', sa.Boolean(), nullable=True))
    op.add_column('Venue', sa.Column('talent_description', sa.String(length=500), nullable=True))
    op.add_column('Venue', sa.Column('website', sa.String(length=120), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Venue', 'website')
    op.drop_column('Venue', 'talent_description')
    op.drop_column('Venue', 'seeking_talent')
    op.drop_column('Artist', 'website')
    op.drop_column('Artist', 'venue_description')
    op.drop_column('Artist', 'seeking_venue')
    # ### end Alembic commands ###
