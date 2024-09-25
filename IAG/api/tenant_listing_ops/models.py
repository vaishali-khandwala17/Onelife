from sqlalchemy import Column, BigInteger, VARCHAR, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TenantDetailsVO(Base):
    __tablename__ = "tenant_details"

    id = Column("id", BigInteger, primary_key=True, autoincrement=True)
    tenant_name = Column("tenant_name", VARCHAR(255), nullable=True)
    username = Column("username", VARCHAR(255), nullable=True)
    tenant_secret_id = Column("tenant_secret_id", VARCHAR(255),
                              nullable=True)
    tenant_secret_key = Column("tenant_secret_key", VARCHAR(255),
                               nullable=True)
    created_at = Column("created_at", DateTime, nullable=True)
    updated_at = Column("updated_at", DateTime, nullable=True)

    def to_dict(self):
        tenant_dict = {
            "id": self.id,
            "tenant_name": self.tenant_name,
            "username": self.username,
            "tenant_secret_id": self.tenant_secret_id,
            "tenant_secret_key": self.tenant_secret_key,
            "created_at": self.created_at.strftime("%Y-%m-%d"),
        }

        return tenant_dict
