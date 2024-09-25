from sqlalchemy import Column, BigInteger, VARCHAR, ForeignKey, Date, \
    DateTime, Integer
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class UserDetailsVO(Base):
    __tablename__ = "user_details"

    id = Column("id", BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey('tenant_details.id'),
                       nullable=False)
    username = Column("username", VARCHAR(255), nullable=True)
    first_name = Column("first_name", VARCHAR(255), nullable=True)
    last_name = Column("last_name", VARCHAR(255), nullable=True)
    dob = Column("dob", Date, nullable=True)
    created_at = Column("created_at", DateTime, nullable=True)
    updated_at = Column("updated_at", DateTime, nullable=True)
    tenant = relationship("TenantDetailsVO", foreign_keys=[tenant_id])

    def to_dict(self):
        user_dict = {
            "id": self.id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "dob": self.dob.strftime("%Y-%m-%d"),

        }

        return user_dict

class RegistrationOtpHistoryVO(Base):
    __tablename__ = "user_otp_history"

    id = Column("id", BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey('tenant_details.id'),
                       nullable=False)
    user_request_id = Column("user_request_id", VARCHAR(255), nullable=True)
    otp = Column("otp", VARCHAR(255), nullable=True)
    otp_expire_time = Column("otp_expire_time", VARCHAR(255), nullable=True)
    user_status = Column("user_status", VARCHAR(255), nullable=True)
    tenant_name = Column("tenant_name", VARCHAR(255), nullable=True)
    username = Column("username", VARCHAR(255), nullable=True)
    created_at = Column("created_at", DateTime, nullable=True)
    updated_at = Column("updated_at", DateTime, nullable=True)
    tenant = relationship("TenantDetailsVO", foreign_keys=[tenant_id])


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