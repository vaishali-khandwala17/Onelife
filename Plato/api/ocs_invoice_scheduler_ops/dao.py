from models import SchedulerVO, InvoicesVO, InvoiceItemVO


class InvoicesDAO:
    @staticmethod
    def insert_invoices(invoice_vo, session):
        session.add(invoice_vo)
        session.commit()

    @staticmethod
    def get_data(session, plato_id):
        data = session.query(InvoicesVO).filter(
            InvoicesVO.plato_id == plato_id).first()
        return data

    @staticmethod
    def update(update_vo, session):
        session.merge(update_vo)
        session.commit()


class InvoiceItemDAO:
    @staticmethod
    def insert_invoices_item(invoice_item_vo, session):
        session.add(invoice_item_vo)
        session.commit()

    @staticmethod
    def get_data(session, invoice_item_id, invoices_id):
        data = session.query(InvoiceItemVO).filter(
            InvoiceItemVO.invoice_item_id == invoice_item_id).filter(
            InvoiceItemVO.invoices_id == invoices_id).first()
        return data

    @staticmethod
    def update(update_vo, session):
        session.merge(update_vo)
        session.commit()


class SchedulerDAO:
    @staticmethod
    def get_data(session, scheduler_name):
        data = session.query(SchedulerVO).filter(
            SchedulerVO.scheduler_name == scheduler_name).first()
        return data

    @staticmethod
    def insert_scheduler(scheduler_vo, session):
        session.add(scheduler_vo)
        session.commit()

    @staticmethod
    def update(update_vo, session):
        session.merge(update_vo)
        session.commit()
