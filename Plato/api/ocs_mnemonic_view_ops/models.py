from sqlalchemy import Column, VARCHAR, BigInteger
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class MnemonicVO(Base):
    __tablename__ = "mnemonic_master"

    id = Column("id", BigInteger, primary_key=True, autoincrement=True)
    cartridge_no = Column("cartridge_no", VARCHAR(255), nullable=True)
    chip_id = Column("chip_id", VARCHAR(255), nullable=True)
    mnemonic = Column("mnemonic", VARCHAR(255), nullable=True)
    commercial_name = Column("commercial_name", VARCHAR(255), nullable=True)

    def to_dict(self):
        patient_dict = {
            "id": self.id,
            "cartridge_no": self.cartridge_no,
            "chip_id": self.chip_id,
            "mnemonic": self.mnemonic,
            "commercial_name": self.commercial_name,
        }
        return patient_dict
