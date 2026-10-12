from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    json_col = sa.JSON().with_variant(postgresql.JSONB, 'postgresql')
    op.add_column('analyses', sa.Column('ai_model', sa.Text(), nullable=True))
    op.add_column('analyses', sa.Column('job_tailored_tips', json_col, nullable=False, server_default='[]'))
    op.add_column('analyses', sa.Column('job_skills', json_col, nullable=False, server_default='[]'))
    op.add_column('analyses', sa.Column('ai_insights', json_col, nullable=True))


def downgrade() -> None:
    op.drop_column('analyses', 'ai_insights')
    op.drop_column('analyses', 'job_skills')
    op.drop_column('analyses', 'job_tailored_tips')
    op.drop_column('analyses', 'ai_model')
