from sqlalchemy import Column, VARCHAR, BigInteger, Time
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class DailyDoseMasterVO(Base):
    __tablename__ = "daily_dose_master"

    id = Column("id", BigInteger, primary_key=True, autoincrement=True)
    dose_abbreviation = Column("dose_abbreviation", VARCHAR(255),
                               nullable=True)
    frequency = Column("frequency", VARCHAR(255), nullable=True)
    interval = Column("interval", VARCHAR(255), nullable=True)
    return_value = Column("return_value", VARCHAR(255), nullable=True)
    default_time = Column("default_time", Time, nullable=True)
    remarks = Column("remarks", VARCHAR(1000), nullable=True)

    def to_dict(self):
        daily_dose_master_dict = {
            "id": self.id,
            "dose_abbreviation": self.dose_abbreviation,
            "frequency": self.frequency,
            "interval": self.interval,
            "return_value": self.return_value,
            "default_time": self.default_time,
            "remarks": self.remarks,
        }
        if daily_dose_master_dict["default_time"]:
            daily_dose_master_dict["default_time"] = self.default_time.strftime('%H:%M:%S')
        return daily_dose_master_dict
