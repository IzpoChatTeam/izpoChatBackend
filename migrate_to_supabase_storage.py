"""Update file_uploads table for Supabase Storage

Revision ID: supabase_storage_migration
Revises: 
Create Date: 2025-09-23 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'supabase_storage_migration'
down_revision = None
depends_on = None


def upgrade() -> None:
    # Crear nueva tabla file_uploads con estructura para Supabase
    op.execute("DROP TABLE IF EXISTS file_uploads CASCADE")
    
    op.create_table('file_uploads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('file_url', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_file_uploads_id'), 'file_uploads', ['id'], unique=False)
    
    # Actualizar tabla messages para apuntar a la nueva estructura
    try:
        op.drop_constraint('messages_file_id_fkey', 'messages', type_='foreignkey')
    except:
        pass  # La constraint puede no existir
    
    op.create_foreign_key(None, 'messages', 'file_uploads', ['file_id'], ['id'])


def downgrade() -> None:
    # Revertir cambios
    op.drop_table('file_uploads')
    
    # Recrear tabla anterior (opcional, para rollback completo)
    op.create_table('file_uploads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('original_filename', sa.String(), nullable=False),
        sa.Column('stored_filename', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('public_url', sa.String(), nullable=False),
        sa.Column('uploader_id', sa.Integer(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['uploader_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_file_uploads_id'), 'file_uploads', ['id'], unique=False)