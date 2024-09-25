from sqlalchemy import Column, BigInteger, VARCHAR, DateTime, Date,Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class PatientVO(Base):
    __tablename__ = "patient"

    id = Column("id", BigInteger, primary_key=True, autoincrement=True)
    given_id = Column("given_id", VARCHAR(255), nullable=True)
    name = Column("name", VARCHAR(255), nullable=False)
    nric = Column("nric", VARCHAR(255), nullable=True)
    dob = Column("dob", Date, nullable=True)
    marital_status = Column("marital_status", VARCHAR(255), nullable=True)
    sex = Column("sex", VARCHAR(255), nullable=True)
    nationality = Column("nationality", VARCHAR(255), nullable=True)
    allergies_select = Column("allergies_select", VARCHAR(255), nullable=True)
    allergies = Column("allergies", VARCHAR(255), nullable=True)
    nric_type = Column("nric_type", VARCHAR(255), nullable=True)
    food_allergies_select = Column("food_allergies_select", VARCHAR(255),
                                   nullable=True)
    food_allergies = Column("food_allergies", VARCHAR(255), nullable=True)
    g6pd = Column("g6pd", VARCHAR(255), nullable=True)
    dial_code = Column("dial_code", VARCHAR(255), nullable=False)
    telephone = Column("telephone", VARCHAR(255), nullable=False)
    alerts = Column("alerts", VARCHAR(255), nullable=True)
    address = Column("address", VARCHAR(255), nullable=False)
    postal = Column("postal", VARCHAR(255), nullable=False)
    unit_no = Column("unit_no", VARCHAR(255), nullable=True)
    email = Column("email", VARCHAR(255), nullable=True)
    telephone2 = Column("telephone2", VARCHAR(255), nullable=True)
    telephone3 = Column("telephone3", VARCHAR(255), nullable=True)
    title = Column("title", VARCHAR(255), nullable=True)
    dnd = Column("dnd", VARCHAR(255), nullable=True)
    occupation = Column("occupation", VARCHAR(255), nullable=True)
    doctor = Column("doctor", VARCHAR(255), nullable=True)
    created_on = Column("created_on", VARCHAR(255), nullable=True)
    created_by = Column("created_by", VARCHAR(255), nullable=True)
    last_edited = Column("last_edited", VARCHAR(255), nullable=True)
    last_edited_by = Column("last_edited_by", VARCHAR(255), nullable=True)
    notes = Column("notes", VARCHAR(255), nullable=True)
    referred_by = Column("referred_by", VARCHAR(255), nullable=True)
    plato_id = Column("plato_id", VARCHAR(255), nullable=True)


class SchedulerVO(Base):
    __tablename__ = "scheduler_job"

    id = Column("id", BigInteger, primary_key=True, autoincrement=True)
    scheduler_name = Column("scheduler_name", VARCHAR(255))
    timestamp = Column("timestamp", Integer)
