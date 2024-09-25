from models import InvoicesVO, PatientVO, InvoiceItemVO


class InvoicesDAO:
    @staticmethod
    def get_data(session, skip, limit, patient_id_filter, invoice_filter,
                 prescription_filter):
        patient_id_filter = "%{}%".format(patient_id_filter)
        invoice_filter = "%{}%".format(invoice_filter)
        if prescription_filter:
            prescription_filter = "%{}%".format(prescription_filter)
            invoices_ids_list = session.query(InvoiceItemVO.invoices_id) \
                .filter(InvoiceItemVO.category.like(prescription_filter)) \
                .distinct() \
                .all()
            filter_invoices_ids = tuple(
                item for tuple_item in invoices_ids_list for item
                in tuple_item)

            data = session.query(InvoicesVO, PatientVO) \
                .join(PatientVO,
                      PatientVO.plato_id == InvoicesVO.patient_id) \
                .filter(PatientVO.given_id.like(patient_id_filter)) \
                .filter(InvoicesVO.invoice.like(invoice_filter)) \
                .filter(InvoicesVO.id.in_(filter_invoices_ids)) \
                .order_by(InvoicesVO.created_on.desc()) \
                .offset(skip).limit(limit).all()
            return data

        data = session.query(InvoicesVO, PatientVO) \
            .join(PatientVO,
                  PatientVO.plato_id == InvoicesVO.patient_id) \
            .filter(PatientVO.given_id.like(patient_id_filter)) \
            .filter(InvoicesVO.invoice.like(invoice_filter)) \
            .order_by(InvoicesVO.created_on.desc()) \
            .offset(skip).limit(limit).all()
        return data
