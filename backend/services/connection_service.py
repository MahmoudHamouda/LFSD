from sqlalchemy.orm import Session
from models.models import Connection
from typing import Optional, List, Dict, Any
import json
import uuid
from datetime import datetime
import core.config
from cryptography.fernet import Fernet
from loguru import logger


class ConnectionService:
    def __init__(self, db: Session):
        self.db = db
        settings = core.config.get_settings()
        if (
            not hasattr(settings, "CREDENTIALS_ENCRYPTION_KEY")
            or not settings.CREDENTIALS_ENCRYPTION_KEY
        ):
            raise ValueError("CREDENTIALS_ENCRYPTION_KEY is missing in configuration.")
        self.fernet = Fernet(settings.CREDENTIALS_ENCRYPTION_KEY.encode())

    def _encrypt(self, data: Dict) -> str:
        """Encrypt dictionary using Fernet."""
        if not data:
            return None
        json_data = json.dumps(data).encode()
        return self.fernet.encrypt(json_data).decode()

    def _decrypt(self, encrypted_str: str) -> Dict:
        """Decrypt string back to dictionary."""
        if not encrypted_str:
            return {}
        try:
            decrypted_data = self.fernet.decrypt(encrypted_str.encode())
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return {}

    def get_connections(self, user_id: str) -> List[Connection]:
        """Get all connections for a user."""
        return self.db.query(Connection).filter(Connection.user_id == user_id).all()

    def get_connection(self, user_id: str, provider: str) -> Optional[Connection]:
        """Get a specific connection for a user."""
        provider = provider.strip().lower()
        return (
            self.db.query(Connection)
            .filter(Connection.user_id == user_id, Connection.provider == provider)
            .first()
        )

    def get_decrypted_credentials(self, user_id: str, provider: str) -> Dict[str, Any]:
        """Fetch and decrypt credentials only when needed."""
        conn = self.get_connection(user_id, provider)
        if not conn or not conn.credentials_json:
            return {}
        return self._decrypt(conn.credentials_json)

    def create_or_update_connection(
        self,
        user_id: str,
        provider: str,
        credentials: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        status: str = "connected",
    ) -> Connection:
        """Create or update a connection with encrypted credentials."""
        provider = provider.strip().lower()
        connection = self.get_connection(user_id, provider)

        try:
            if connection:
                # Security Rule: Never overwrite credentials with an empty dict
                if credentials and credentials != {}:
                    connection.credentials_json = self._encrypt(credentials)

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
                    credentials_json=(
                        self._encrypt(credentials) if credentials else None
                    ),
                    metadata_json=json.dumps(metadata or {}),
                )
                self.db.add(connection)

            self.db.commit()
            self.db.refresh(connection)
            return connection
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create/update connection: {e}")
            raise e

    def revoke_connection(self, user_id: str, provider: str) -> bool:
        """Revoke a connection: wipe credentials but keep the record for audit."""
        provider = provider.strip().lower()
        connection = self.get_connection(user_id, provider)
        if connection:
            try:
                connection.status = "revoked"
                connection.credentials_json = None  # Wipe sensitive data
                connection.updated_at = datetime.utcnow()
                self.db.commit()
                return True
            except Exception as e:
                self.db.rollback()
                logger.error(f"Failed to revoke connection: {e}")
                return False
        return False

    def delete_connection(self, user_id: str, provider: str) -> bool:
        """Permanently delete a connection."""
        provider = provider.strip().lower()
        connection = self.get_connection(user_id, provider)
        if connection:
            try:
                self.db.delete(connection)
                self.db.commit()
                return True
            except Exception as e:
                self.db.rollback()
                logger.error(f"Failed to delete connection: {e}")
                return False
        return False
