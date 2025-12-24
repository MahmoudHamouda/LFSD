"""
Service for managing user connections to external providers.
"""
from sqlalchemy.orm import Session
from models.models import Connection
from typing import Optional, List, Dict
import json
import uuid
from datetime import datetime
from core.config import get_settings

class ConnectionService:
    def __init__(self, db: Session):
        self.db = db

    def get_connections(self, user_id: str) -> List[Connection]:
        """Get all connections for a user."""
        return self.db.query(Connection).filter(Connection.user_id == user_id).all()

    def get_connection(self, user_id: str, provider: str) -> Optional[Connection]:
        """Get a specific connection for a user."""
        return self.db.query(Connection).filter(
            Connection.user_id == user_id,
            Connection.provider == provider
        ).first()

    def create_or_update_connection(
        self, 
        user_id: str, 
        provider: str, 
        credentials: Dict, 
        metadata: Dict = None,
        status: str = "connected"
    ) -> Connection:
        """Create or update a connection."""
        connection = self.get_connection(user_id, provider)
        
        if connection:
            connection.credentials_json = json.dumps(credentials)
            connection.status = status
            if metadata:
                connection.metadata_json = json.dumps(metadata)
            connection.updated_at = datetime.utcnow()
        else:
            connection = Connection(
                id=str(uuid.uuid4()),
                user_id=user_id,
                provider=provider,
                status=status,
                credentials_json=json.dumps(credentials),
                metadata_json=json.dumps(metadata or {})
            )
            self.db.add(connection)
        
        self.db.commit()
        self.db.refresh(connection)
        return connection

    def delete_connection(self, user_id: str, provider: str) -> bool:
        """Delete a connection."""
        connection = self.get_connection(user_id, provider)
        if connection:
            self.db.delete(connection)
            self.db.commit()
            return True
        return False
