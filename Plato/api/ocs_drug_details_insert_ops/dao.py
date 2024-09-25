from models import InvoicesVO, PatientVO, InvoiceItemVO


class DrugDetailsDAO:
    @staticmethod
    def insert_drug_detail(drug_vo, session):
        session.add(drug_vo)
        session.commit()


class InvoicesDAO:
    @staticmethod
    def get_data(session, invoices_id):
        data = session.query(InvoicesVO, PatientVO) \
            .join(PatientVO,
                  PatientVO.plato_id == InvoicesVO.patient_id) \
            .filter(InvoicesVO.id == invoices_id).first()
        return data

    @staticmethod
    def update(update_vo, session):
        session.merge(update_vo)
        session.commit()


class InvoicesItemDAO:
    @staticmethod
    def get_data(session, invoice_item_id):
        data = session.query(InvoiceItemVO) \
            .filter(InvoiceItemVO.id == invoice_item_id).first()
        return data
