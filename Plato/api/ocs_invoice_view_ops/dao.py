from models import InvoicesVO, PatientVO, InvoiceItemVO, DrugDetailsVO


class InvoicesDAO:
    @staticmethod
    def get_data(session, invoices_id):
        data = session.query(InvoicesVO, PatientVO) \
            .join(PatientVO,
                  PatientVO.plato_id == InvoicesVO.patient_id) \
            .filter(InvoicesVO.id == invoices_id).first()
        return data

    @staticmethod
    def insert_patient(patient_vo, session):
        session.add(patient_vo)
        session.commit()

    @staticmethod
    def get_one_data(session, invoices_id):
        data = session.query(InvoicesVO) \
            .filter(InvoicesVO.id == invoices_id).first()
        return data

    @staticmethod
    def update(update_vo, session):
        session.merge(update_vo)
        session.commit()


class InvoicesItemDAO:
    @staticmethod
    def get_data(session, invoices_id):
        data = session.query(InvoiceItemVO).filter(
            InvoiceItemVO.invoices_id == invoices_id).all()
        return data


class PatientDAO:
    @staticmethod
    def insert_patient(patient_vo, session):
        session.add(patient_vo)
        session.commit()


class DrugDetailsDAO:
    @staticmethod
    def get_data(session, invoice_item_id):
        data = session.query(DrugDetailsVO).filter(
            DrugDetailsVO.invoices_item_id == invoice_item_id).first()
        return data
