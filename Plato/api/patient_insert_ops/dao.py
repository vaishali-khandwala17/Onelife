class PatientDAO:
    @staticmethod
    def insert_patient(patient_vo, session):
        session.add(patient_vo)
        session.commit()

    @staticmethod
    def update_patient(patient_vo, session):
        session.merge(patient_vo)
        session.commit()

