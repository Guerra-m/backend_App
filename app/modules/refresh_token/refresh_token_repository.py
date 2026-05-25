from datetime import datetime, timezone
from sqlmodel import Session, select
from app.modules.refresh_token.refresh_token_model import RefreshToken
from app.core.base_repository import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, session: Session):
        super().__init__(RefreshToken, session)

    def create(self, token: RefreshToken) -> RefreshToken:
        self.session.add(token)
        self.session.flush()
        return token

    def get_valid_by_hash(self, token_hash: str) -> RefreshToken | None:
        """
        Busca un refresh token válido:
        - Coincide hash
        - No expirado (expires_at > now)
        - No revocado (revoked_at IS NULL)
        """
        now = datetime.now(timezone.utc)
        statement = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.expires_at > now,
            RefreshToken.revoked_at == None,
        )
        return self.session.exec(statement).first()

    def revoke(self, token: RefreshToken) -> None:
        """Marca el token como revocado (revoked_at = now)."""
        token.revoked_at = datetime.now(timezone.utc)
        self.session.add(token)
        self.session.flush()

    def revoke_all_by_usuario(self, usuario_id: int) -> None:
        """Revoca todos los refresh tokens activos del usuario (logout seguro)."""
        now = datetime.now(timezone.utc)
        statement = select(RefreshToken).where(
            RefreshToken.usuario_id == usuario_id,
            RefreshToken.revoked_at == None,
        )
        tokens = self.session.exec(statement).all()
        for token in tokens:
            token.revoked_at = now
            self.session.add(token)
        self.session.flush()
