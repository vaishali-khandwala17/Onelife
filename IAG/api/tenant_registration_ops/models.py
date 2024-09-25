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
