from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '2b0da67a9354'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('analyses', sa.Column('summary_feedback', sa.Text(), nullable=True))
    op.add_column('analyses', sa.Column('ai_unavailable', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('analyses', 'ai_unavailable')
    op.drop_column('analyses', 'summary_feedback')
