"""add_llm_connections

Revision ID: 8e6f32050015
Revises: ca20728c080d
Create Date: 2026-05-20 20:08:00.000000

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

from dataline.utils.encryption import encrypt

# revision identifiers, used by Alembic.
revision: str = '8e6f32050015'
down_revision: Union[str, None] = 'ca20728c080d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create llm_connection table
    llm_conn_table = op.create_table(
        'llm_connection',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('model', sa.String(), nullable=False),
        sa.Column('api_key', sa.String(), nullable=True),
        sa.Column('base_url', sa.String(), nullable=True),
        sa.Column('is_default', sa.Boolean(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Migrate existing user OpenAI settings to llm_connection
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    
    if 'user' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('user')]
        
        # Only migrate if the old columns exist
        if 'openai_api_key' in columns or 'preferred_openai_model' in columns or 'openai_base_url' in columns:
            users = bind.execute(sa.text("SELECT id, openai_api_key, preferred_openai_model, openai_base_url FROM user")).fetchall()
            
            for user in users:
                user_id, api_key, model, base_url = user
                if api_key or model:
                    encrypted_key = encrypt(api_key) if api_key else None
                    chosen_model = model if model else "gpt-3.5-turbo"
                    conn_id = str(uuid.uuid4())
                    
                    bind.execute(
                        sa.text(
                            "INSERT INTO llm_connection (id, provider, model, api_key, base_url, is_default) "
                            "VALUES (:id, :provider, :model, :api_key, :base_url, :is_default)"
                        ),
                        {
                            "id": conn_id,
                            "provider": "openai",
                            "model": chosen_model,
                            "api_key": encrypted_key,
                            "base_url": base_url,
                            "is_default": 1
                        }
                    )

            # Drop columns from user table (using batch_alter_table for SQLite compatibility)
            # Only drop if columns exist
            with op.batch_alter_table('user') as batch_op:
                if 'openai_api_key' in columns:
                    batch_op.drop_column('openai_api_key')
                if 'preferred_openai_model' in columns:
                    batch_op.drop_column('preferred_openai_model')
                if 'openai_base_url' in columns:
                    batch_op.drop_column('openai_base_url')


def downgrade() -> None:
    # Add columns back to user
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(sa.Column('openai_api_key', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('preferred_openai_model', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('openai_base_url', sa.String(), nullable=True))

    bind = op.get_bind()
    
    # Try to restore the default connection back to user
    default_conn = bind.execute(sa.text("SELECT api_key, model, base_url FROM llm_connection WHERE is_default = 1 AND provider = 'openai' LIMIT 1")).fetchone()
    
    if default_conn:
        from dataline.utils.encryption import decrypt
        enc_api_key, model, base_url = default_conn
        api_key = decrypt(enc_api_key) if enc_api_key else None
        
        # Just update all users with this for downgrade
        bind.execute(
            sa.text("UPDATE user SET openai_api_key = :api_key, preferred_openai_model = :model, openai_base_url = :base_url"),
            {"api_key": api_key, "model": model, "base_url": base_url}
        )

    # Drop llm_connection table
    op.drop_table('llm_connection')
