"""数据库迁移脚本

添加智能分析相关字段到 daily_reports 表
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = 'add_smart_analysis_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """添加智能分析字段"""
    # 添加新字段
    op.add_column('daily_reports', sa.Column('smart_analysis', sa.Text(), nullable=True))
    op.add_column('daily_reports', sa.Column('smart_analysis_formatted', sa.Text(), nullable=True))
    op.add_column('daily_reports', sa.Column('pmr_data', sa.Text(), nullable=True))
    op.add_column('daily_reports', sa.Column('llm_model', sa.String(50), nullable=True))
    op.add_column('daily_reports', sa.Column('llm_provider', sa.String(50), nullable=True))
    
    print("[OK] 成功添加智能分析字段到 daily_reports 表")


def downgrade():
    """移除智能分析字段"""
    op.drop_column('daily_reports', 'llm_provider')
    op.drop_column('daily_reports', 'llm_model')
    op.drop_column('daily_reports', 'pmr_data')
    op.drop_column('daily_reports', 'smart_analysis_formatted')
    op.drop_column('daily_reports', 'smart_analysis')
    
    print("[OK] 成功移除智能分析字段")
