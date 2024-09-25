from sqlalchemy import Column, VARCHAR, BigInteger, Date, Time, Integer, \
    ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class InvoicesVO(Base):
    __tablename__ = "invoices"

    id = Column("id", BigInteger, primary_key=True, autoincrement=True)
    plato_id = Column("plato_id", VARCHAR(255), nullable=True)
    invoice_status = Column("invoice_status", VARCHAR(255), nullable=True)
    patient_id = Column("patient_id", VARCHAR(255), nullable=True)
    location = Column("location", VARCHAR(255), nullable=True)
    date = Column("date", Date, nullable=True)
    no_gst = Column("no_gst", VARCHAR(255), nullable=True)
    doctor = Column("doctor", VARCHAR(255), nullable=True)
    adj = Column("adj", VARCHAR(255), nullable=True)
    highlight = Column("highlight", VARCHAR(255), nullable=True)
    status = Column("status", VARCHAR(255), nullable=True)
    status_on = Column("status_on", DateTime, nullable=True)
    rate = Column("rate", VARCHAR(255), nullable=True)
    sub_total = Column("sub_total", VARCHAR(255),
                       nullable=True)
    tax = Column("tax", VARCHAR(255), nullable=True)
    total = Column("total", VARCHAR(255), nullable=True)
    adj_amount = Column("adj_amount", VARCHAR(255), nullable=True)
    finalized = Column("finalized", VARCHAR(255), nullable=True)
    finalized_on = Column("finalized_on", DateTime, nullable=True)
    finalized_by = Column("finalized_by", VARCHAR(255), nullable=True)
    invoice_prefix = Column("invoice_prefix", VARCHAR(255), nullable=True)
    invoice = Column("invoice", VARCHAR(255), nullable=True)
    invoices_batch = Column("invoices_batch", VARCHAR(255), nullable=True)
    notes = Column("notes", VARCHAR(255), nullable=True)
    corp_notes = Column("corp_notes", VARCHAR(255), nullable=True)
    invoice_notes = Column("invoice_notes", VARCHAR(255), nullable=True)
    created_by = Column("created_by", VARCHAR(255), nullable=True)
    created_on = Column("created_on", DateTime, nullable=True)
    last_edited = Column("last_edited", DateTime, nullable=True)
    last_edited_by = Column("last_edited_by", VARCHAR(255), nullable=True)
    void = Column("void", VARCHAR(255), nullable=True)
    void_reason = Column("void_reason", VARCHAR(255), nullable=True)
    void_on = Column("void_on", DateTime, nullable=True)
    void_by = Column("void_by", VARCHAR(255), nullable=True)
    session = Column("session", VARCHAR(255), nullable=True)
    manual_timein = Column("manual_timein", DateTime, nullable=True)
    manual_timeout = Column("manual_timeout", DateTime, nullable=True)
    cndn = Column("cndn", VARCHAR(255), nullable=True)
    cndn_apply_to = Column("cndn_apply_to", VARCHAR(255), nullable=True)

    def to_dict(self):
        invoices_dict = {
            "invoices_batch": self.invoices_batch,
            "invoice": self.invoice,
            "created_on": self.created_on.strftime("%Y-%m-%d %H:%M:%S")
        }
        return invoices_dict


class DrugDetailsVO(Base):
    __tablename__ = "drug_details"

    id = Column("id", BigInteger, primary_key=True, autoincrement=True)
    invoices_item_id = Column(Integer, ForeignKey('invoices_items.id'),
                              nullable=False)
    drug_id = Column("drug_id", VARCHAR(255), nullable=True)
    qty = Column("qty", VARCHAR(255), nullable=True)
    start_date = Column("start_date", Date, nullable=True)
    end_date = Column("end_date", Date, nullable=True)
    admin_time = Column("admin_time", Time, nullable=True)
    batch = Column("batch", VARCHAR(255), nullable=True)
    admin_description = Column("admin_description", VARCHAR(255),
                               nullable=True)
    random_1 = Column("random_1", VARCHAR(255), nullable=True)
    random_2 = Column("random_2", VARCHAR(255), nullable=True)
    random_3 = Column("random_3", VARCHAR(255), nullable=True)
    random_4 = Column("random_4", VARCHAR(255), nullable=True)
    random_5 = Column("random_5", VARCHAR(255), nullable=True)
    invoices = relationship("InvoiceItemVO", foreign_keys=[invoices_item_id])


class PatientVO(Base):
    __tablename__ = "patient"

    id = Column("id", BigInteger, primary_key=True, autoincrement=True)
    given_id = Column("given_id", VARCHAR(255), nullable=True)
    name = Column("name", VARCHAR(255), nullable=False)
    nric = Column("nric", VARCHAR(255), nullable=True)
    dob = Column("dob", Date, nullable=False)
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

    def to_dict(self):
        patient_dict = {
            "patient_name": self.name,
            "patient_id": self.given_id
        }
        return patient_dict


class InvoiceItemVO(Base):
    __tablename__ = "invoices_items"

    id = Column("id", BigInteger, primary_key=True, autoincrement=True)
    invoice_item_id = Column("invoice_item_id", VARCHAR(255), nullable=True)
    invoices_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    qty = Column("qty", VARCHAR(255), nullable=True)
    name = Column("name", VARCHAR(255), nullable=True)
    unit = Column("unit", VARCHAR(255), nullable=True)
    ddose = Column("ddose", VARCHAR(255), nullable=True)
    dfreq = Column("dfreq", VARCHAR(255), nullable=True)
    dunit = Column("dunit", VARCHAR(255), nullable=True)
    dosage = Column("dosage", VARCHAR(255), nullable=True)
    hidden = Column("hidden", VARCHAR(255), nullable=True)
    category = Column("category", VARCHAR(255), nullable=True)
    disc_abs = Column("disc_abs", VARCHAR(255), nullable=True)
    discount = Column("discount", VARCHAR(255),
                      nullable=True)
    facility = Column("facility", VARCHAR(255), nullable=True)
    given_id = Column("given_id", VARCHAR(255), nullable=True)
    batch_cpu = Column("batch_cpu", VARCHAR(255), nullable=True)
    dduration = Column("dduration", VARCHAR(255), nullable=True)
    inventory = Column("inventory", VARCHAR(255), nullable=True)
    min_price = Column("min_price", VARCHAR(255), nullable=True)
    sub_total = Column("sub_total", VARCHAR(255), nullable=True)
    cost_price = Column("cost_price", VARCHAR(255), nullable=True)
    invoice_id = Column("invoice_id", VARCHAR(255), nullable=True)
    redeemable = Column("redeemable", VARCHAR(255), nullable=True)
    unit_price = Column("unit_price", VARCHAR(255), nullable=True)
    batch_batch = Column("batch_batch", VARCHAR(255), nullable=True)
    description = Column("description", VARCHAR(255), nullable=True)
    fixed_price = Column("fixed_price", VARCHAR(255), nullable=True)
    last_edited = Column("last_edited", DateTime, nullable=True)
    no_discount = Column("no_discount", VARCHAR(255), nullable=True)
    precautions = Column("precautions", VARCHAR(255), nullable=True)
    redemptions = Column("redemptions", VARCHAR(255), nullable=True)
    track_stock = Column("track_stock", VARCHAR(255), nullable=True)
    batch_expiry = Column("batch_expiry", VARCHAR(255), nullable=True)
    facility_due = Column("facility_due", Date, nullable=True)
    facility_ref = Column("facility_ref", VARCHAR(255), nullable=True)
    facility_paid = Column("facility_paid", VARCHAR(255), nullable=True)
    selling_price = Column("selling_price", VARCHAR(255), nullable=True)
    last_edited_by = Column("last_edited_by", VARCHAR(255), nullable=True)
    facility_status = Column("facility_status", VARCHAR(255), nullable=True)
    package_original_price = Column("package_original_price", VARCHAR(255),
                                    nullable=True)
    expiry_after_dispensing = Column("expiry_after_dispensing", VARCHAR(255),
                                     nullable=True)
    invoices = relationship("InvoicesVO", foreign_keys=[invoices_id])

    def to_dict(self):
        invoice_item_data = {
            "invoice_item_id": self.invoice_item_id
        }
        return invoice_item_data
