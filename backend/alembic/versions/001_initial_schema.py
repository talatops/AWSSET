"""Initial schema migration

Revision ID: 001_initial
Revises: 
Create Date: 2025-02-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=True),
        sa.Column('provider', sa.String(), nullable=False, server_default='local'),
        sa.Column('provider_id', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('profile_customized', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('aws_access_key', sa.String(), nullable=True),
        sa.Column('aws_secret_key', sa.String(), nullable=True),
        sa.Column('aws_region', sa.String(), nullable=True, server_default='us-east-1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create chat_sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_sessions_id'), 'chat_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_chat_sessions_session_id'), 'chat_sessions', ['session_id'], unique=True)
    op.create_index(op.f('ix_chat_sessions_user_id'), 'chat_sessions', ['user_id'], unique=False)

    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('message_type', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('aws_service', sa.String(), nullable=True),
        sa.Column('operation_type', sa.String(), nullable=True),
        sa.Column('operation_status', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_messages_id'), 'chat_messages', ['id'], unique=False)

    # Create aws_resources table
    op.create_table(
        'aws_resources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=False),
        sa.Column('resource_name', sa.String(), nullable=True),
        sa.Column('resource_arn', sa.String(), nullable=True),
        sa.Column('region', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_via_chat', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_aws_resources_id'), 'aws_resources', ['id'], unique=False)

    # Create system_logs table
    op.create_table(
        'system_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('level', sa.String(), nullable=False),
        sa.Column('service', sa.String(), nullable=False),
        sa.Column('operation', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_logs_id'), 'system_logs', ['id'], unique=False)

    # Create cloudtrail_events table
    op.create_table(
        'cloudtrail_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(), nullable=False),
        sa.Column('event_name', sa.String(), nullable=False),
        sa.Column('event_source', sa.String(), nullable=False),
        sa.Column('event_time', sa.DateTime(), nullable=False),
        sa.Column('user_identity', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('aws_region', sa.String(), nullable=True),
        sa.Column('source_ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('request_parameters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('response_elements', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('additional_event_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('api_version', sa.String(), nullable=True),
        sa.Column('read_only', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('management_event', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('insight_details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ai_analysis', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('anomaly_detected', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('security_incident', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('cost_impact', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cloudtrail_events_event_id'), 'cloudtrail_events', ['event_id'], unique=True)
    op.create_index(op.f('ix_cloudtrail_events_event_name'), 'cloudtrail_events', ['event_name'], unique=False)
    op.create_index(op.f('ix_cloudtrail_events_event_source'), 'cloudtrail_events', ['event_source'], unique=False)
    op.create_index(op.f('ix_cloudtrail_events_event_time'), 'cloudtrail_events', ['event_time'], unique=False)
    op.create_index(op.f('ix_cloudtrail_events_id'), 'cloudtrail_events', ['id'], unique=False)

    # Create security_incidents table
    op.create_table(
        'security_incidents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True, server_default='open'),
        sa.Column('incident_type', sa.String(), nullable=False),
        sa.Column('related_events', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ai_analysis', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('recommended_actions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('estimated_cost_impact', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('actual_cost_impact', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_security_incidents_id'), 'security_incidents', ['id'], unique=False)
    op.create_index(op.f('ix_security_incidents_incident_id'), 'security_incidents', ['incident_id'], unique=True)
    op.create_index(op.f('ix_security_incidents_severity'), 'security_incidents', ['severity'], unique=False)
    op.create_index(op.f('ix_security_incidents_status'), 'security_incidents', ['status'], unique=False)
    op.create_index(op.f('ix_security_incidents_incident_type'), 'security_incidents', ['incident_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_security_incidents_incident_type'), table_name='security_incidents')
    op.drop_index(op.f('ix_security_incidents_status'), table_name='security_incidents')
    op.drop_index(op.f('ix_security_incidents_severity'), table_name='security_incidents')
    op.drop_index(op.f('ix_security_incidents_incident_id'), table_name='security_incidents')
    op.drop_index(op.f('ix_security_incidents_id'), table_name='security_incidents')
    op.drop_table('security_incidents')
    
    op.drop_index(op.f('ix_cloudtrail_events_id'), table_name='cloudtrail_events')
    op.drop_index(op.f('ix_cloudtrail_events_event_time'), table_name='cloudtrail_events')
    op.drop_index(op.f('ix_cloudtrail_events_event_source'), table_name='cloudtrail_events')
    op.drop_index(op.f('ix_cloudtrail_events_event_name'), table_name='cloudtrail_events')
    op.drop_index(op.f('ix_cloudtrail_events_event_id'), table_name='cloudtrail_events')
    op.drop_table('cloudtrail_events')
    
    op.drop_index(op.f('ix_system_logs_id'), table_name='system_logs')
    op.drop_table('system_logs')
    
    op.drop_index(op.f('ix_aws_resources_id'), table_name='aws_resources')
    op.drop_table('aws_resources')
    
    op.drop_index(op.f('ix_chat_messages_id'), table_name='chat_messages')
    op.drop_table('chat_messages')
    
    op.drop_index(op.f('ix_chat_sessions_user_id'), table_name='chat_sessions')
    op.drop_index(op.f('ix_chat_sessions_session_id'), table_name='chat_sessions')
    op.drop_index(op.f('ix_chat_sessions_id'), table_name='chat_sessions')
    op.drop_table('chat_sessions')
    
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
