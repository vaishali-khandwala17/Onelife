from models import SchedulerVO,PatientVO


class SchedulerDAO:
    @staticmethod
    def get_data(session, scheduler_name):
        data = session.query(SchedulerVO).filter(
            SchedulerVO.scheduler_name == scheduler_name).first()
        return data

    @staticmethod
    def insert_patient(patient_vo, session):
        session.add(patient_vo)
        session.commit()

    @staticmethod
    def insert_scheduler(patient_vo, session):
        session.add(patient_vo)
        session.commit()

    @staticmethod
    def update(update_vo, session):
        session.merge(update_vo)
        session.commit()

class PatientDAO:
    @staticmethod
    def patient_get_data(plato_id,session):
        data = session.query(PatientVO).filter(PatientVO.plato_id ==
                                               plato_id).first()
        return data

    @staticmethod
    def update_patient(patient_vo, session):
        session.merge(patient_vo)
        session.commit()