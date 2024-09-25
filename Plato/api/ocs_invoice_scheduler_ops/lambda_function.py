import logging
import time
from datetime import datetime
import requests
import random
from configparser import ConfigParser
from config import db_connection
from services import AppServices
from dao import InvoicesDAO, InvoiceItemDAO, SchedulerDAO
from models import InvoicesVO, InvoiceItemVO, SchedulerVO, Base

logger = logging.getLogger("ksi_plato_invoice_operations")
logger.setLevel(logging.INFO)

configure = ConfigParser()
configure.read('config.ini')

ERROR_FORMAT = configure.get('ERROR_HANDLING', 'format')
API_URL = configure.get('DEV_PLATO_API', 'api_url')
INVOICE_VIEW_URL = configure.get('DEV_PLATO_API', 'invoice_post_url')
API_TOKEN = configure.get('DEV_PLATO_API', 'api_token')
PAGE_LIMIT = int(configure.get('DEV_PLATO_API', 'page_limit'))
API_DELAY = float(configure.get('DEV_PLATO_API', 'api_delay'))
SCHEDULER_NAME = configure.get('COMMON_CONFIG', 'scheduler_name')
DEFAULT_INVOICE_STATUS = configure.get('COMMON_CONFIG',
                                       'default_invoice_status')
INVOICE_BATCH_NUMBER_LENGTH = configure.get('COMMON_CONFIG',
                                            'invoice_batch_number_length')


def randN(N):
    min = pow(10, N - 1)
    max = pow(10, N) - 1
    return random.randint(min, max)


def lambda_handler(event, context):
    logger.info("got event = {}".format(event))
    logger.info("got context = {}".format(context))

    date_time = datetime.utcnow().replace(microsecond=0)
    current_time = int(time.mktime(date_time.timetuple()))

    server_alias = AppServices.get_env(context)
    logger.info("got env = {}".format(server_alias))

    db_engine, session = db_connection(server_alias)
    Base.metadata.create_all(db_engine)

    response_payload = plato_invoice_ops(session, current_time)
    logger.info("Final response_payload = {}".format(response_payload))
    return response_payload


def plato_invoice_ops(session, current_time):
    logger.info("Function: plato_invoice_ops")
    logger.info("Params: session = {}, current_time = {}".format(session,
                                                                 current_time))
    try:
        modified_since = None
        scheduler_id = None
        scheduler_name = SCHEDULER_NAME
        data = SchedulerDAO.get_data(session, scheduler_name)
        if data:
            scheduler_id = data.id
            modified_since = data.timestamp

        is_fetch_success = plato_invoice_fetch_api(modified_since, session)
        logger.info("is_fetch_success = {}".format(is_fetch_success))

        if not is_fetch_success:
            message = "Something went wrong!!"
            response_payload = AppServices.app_response(500, message, False,
                                                        {})
            return response_payload

        is_update_success = update_timestamp(scheduler_id, session,
                                             current_time)
        logger.info("is_update_success = {}".format(is_update_success))

        if not is_update_success:
            message = "Something went wrong!!"
            response_payload = AppServices.app_response(500, message, False,
                                                        {})
            return response_payload

        message = "invoice Details insert success"
        response_payload = AppServices.app_response(200, message, True,
                                                    {})
        return response_payload

    except Exception as e:
        logger.info("Function plato_invoice_ops got error = {}".format(e))
        message = "Something went wrong!!"
        response_payload = AppServices.app_response(500, message, False, {})
        return response_payload


def plato_invoice_fetch_api(modified_since, session):
    logger.info("Function: plato_fetch_api")
    logger.info("Params: modified_since = {}".format(modified_since))
    try:
        headers = {'Authorization': "Bearer {}".format(API_TOKEN)}
        api_call = ""
        current_page = 1
        api_flag = True
        while api_flag:
            if modified_since:
                api_call = '{}{}'.format(API_URL, INVOICE_VIEW_URL +
                                         f"&current_page={current_page}" +
                                         f"&modified_since={modified_since}")
            else:
                api_call = '{}{}'.format(API_URL,
                                         INVOICE_VIEW_URL +
                                         f"&current_page={current_page}")

            api_response = requests.get(api_call, headers=headers).json()
            logger.info(
                "API = {}, API response = {}".format(api_call, api_response))
            current_page = current_page + 1
            if api_response:
                time.sleep(API_DELAY)
                for invoice_data in api_response:
                    invoice_items = invoice_data.get("item")
                    if not invoice_items:
                        invoice_items = []
                    is_insert, invoices_id, is_update = invoice_insert_db(
                        invoice_data, session)
                    logger.info("invoice_data = {}, is_insert = {}".format(
                        invoice_data, is_insert))
                    for invoice_items in invoice_items:
                        is_insert = invoice_item_insert_db(is_update,
                                                           invoice_items,
                                                           invoices_id,
                                                           session)
                        logger.info("invoice_data = {}, is_insert = {}".format(
                            invoice_data, is_insert))
            else:
                api_flag = False
                break

        return True

    except Exception as e:
        logger.info("Function plato_fetch_api got error = {}".format(e))
        return False


def invoice_insert_db(invoice_data, session):
    logger.info("Function: patient_insert_db")
    logger.info("Param: invoice_data = {}".format(invoice_data))
    try:
        invoices_batch_number = str(invoice_data.get('invoice')) + str(int(
            datetime.strptime(invoice_data.get('created_on'),
                              "%Y-%m-%d %H:%M:%S").timestamp()))
        invoices_batch_random = str(invoices_batch_number) + str(
            randN(int(INVOICE_BATCH_NUMBER_LENGTH) - len(
                invoices_batch_number)))

        invoice_vo = InvoicesVO()
        plato_id = invoice_data.get('_id')
        data = InvoicesDAO.get_data(session, plato_id)
        if invoice_data.get('date') != '0000-00-00':
            invoice_vo.date = invoice_data.get('date')
        if invoice_data.get('status_on') != '0000-00-00 00:00:00':
            invoice_vo.status_on = invoice_data.get('status_on')
        if invoice_data.get('finalized_on') != '0000-00-00 00:00:00':
            invoice_vo.finalized_on = invoice_data.get('finalized_on')
        if invoice_data.get('created_on') != '0000-00-00 00:00:00':
            invoice_vo.created_on = invoice_data.get('created_on')
        if invoice_data.get('last_edited') != '0000-00-00 00:00:00':
            invoice_vo.last_edited = invoice_data.get('last_edited')
        if invoice_data.get('void_on') != '0000-00-00 00:00:00':
            invoice_vo.void_on = invoice_data.get('void_on')
        if invoice_data.get('manual_timein') != '0000-00-00 00:00:00':
            invoice_vo.manual_timein = invoice_data.get('manual_timein')
        if invoice_data.get('manual_timeout') != '0000-00-00 00:00:00':
            invoice_vo.manual_timeout = invoice_data.get('manual_timeout')
        invoice_vo.invoices_batch = invoices_batch_random
        invoice_vo.plato_id = plato_id
        invoice_vo.invoice_status = DEFAULT_INVOICE_STATUS
        invoice_vo.patient_id = invoice_data.get('patient_id')
        invoice_vo.location = invoice_data.get('location')
        invoice_vo.no_gst = invoice_data.get('no_gst')
        invoice_vo.doctor = invoice_data.get('doctor')
        invoice_vo.adj = invoice_data.get('adj')
        invoice_vo.highlight = invoice_data.get('highlight')
        invoice_vo.status = invoice_data.get('status')
        invoice_vo.rate = invoice_data.get('rate')
        invoice_vo.sub_total = invoice_data.get('sub_total')
        invoice_vo.tax = invoice_data.get('tax')
        invoice_vo.total = invoice_data.get('total')
        invoice_vo.adj_amount = invoice_data.get('adj_amount')
        invoice_vo.finalized = invoice_data.get('finalized')
        invoice_vo.finalized_by = invoice_data.get('finalized_by')
        invoice_vo.invoice_prefix = invoice_data.get('invoice_prefix')
        invoice_vo.invoice = invoice_data.get('invoice')
        invoice_vo.notes = invoice_data.get('notes')
        invoice_vo.corp_notes = invoice_data.get('corp_notes')
        invoice_vo.invoice_notes = invoice_data.get('invoice_notes')
        invoice_vo.created_by = invoice_data.get('created_by')
        invoice_vo.last_edited_by = invoice_data.get('last_edited_by')
        invoice_vo.void = invoice_data.get('void')
        invoice_vo.void_reason = invoice_data.get('void_reason')

        invoice_vo.void_by = invoice_data.get('void_by')
        invoice_vo.session = invoice_data.get('session')

        invoice_vo.cndn = invoice_data.get('cndn')
        invoice_vo.cndn_apply_to = invoice_data.get('cndn_apply_to')
        if data:
            is_update = True
            logger.info("Data already exist!!")
            invoice_vo.id = data.id
            InvoicesDAO.update(invoice_vo, session)
        else:
            is_update = False
            logger.info("New Data Insert!!")
            InvoicesDAO.insert_invoices(invoice_vo, session)
        return True, invoice_vo.id, is_update

    except Exception as e:
        logger.error("Function patient_insert_db got error = {}".format(e))
        return False, None, False


def invoice_item_insert_db(is_update, invoice_items_data, invoices_id,
                           session):
    logger.info("Function: invoice_item_insert_db")
    logger.info(
        "Param:is_update = {}, invoice_items = {}, invoices_id = {}".format(
            is_update, invoice_items_data, invoices_id))
    try:
        invoice_items_vo = InvoiceItemVO()
        invoice_item_id = str(invoice_items_data.get('_id'))
        if invoice_items_data.get('facility_due') != '0000-00-00':
            invoice_items_vo.facility_due = invoice_items_data.get(
                'facility_due')
        if invoice_items_data.get(
                'last_edited') != "0000-00-00 00:00:00.000000":
            invoice_items_vo.last_edited = invoice_items_data.get(
                'last_edited')
        invoice_items_vo.invoice_item_id = invoice_item_id
        invoice_items_vo.invoices_id = invoices_id
        invoice_items_vo.qty = invoice_items_data.get('qty')
        invoice_items_vo.name = invoice_items_data.get('name')
        invoice_items_vo.unit = invoice_items_data.get('unit')
        invoice_items_vo.ddose = invoice_items_data.get('ddose')
        invoice_items_vo.dfreq = invoice_items_data.get('dfreq')
        invoice_items_vo.dunit = invoice_items_data.get('dunit')
        invoice_items_vo.dosage = invoice_items_data.get('dosage')
        invoice_items_vo.hidden = invoice_items_data.get('hidden')
        invoice_items_vo.category = invoice_items_data.get('category')
        invoice_items_vo.disc_abs = invoice_items_data.get('disc_abs')
        invoice_items_vo.discount = invoice_items_data.get('discount')
        invoice_items_vo.facility = invoice_items_data.get('facility')
        invoice_items_vo.given_id = invoice_items_data.get('given_id')
        invoice_items_vo.batch_cpu = invoice_items_data.get('batch_cpu')
        invoice_items_vo.dduration = invoice_items_data.get('dduration')
        invoice_items_vo.inventory = invoice_items_data.get('inventory')
        invoice_items_vo.min_price = invoice_items_data.get('min_price')
        invoice_items_vo.sub_total = invoice_items_data.get('sub_total')
        invoice_items_vo.cost_price = invoice_items_data.get('cost_price')
        invoice_items_vo.invoice_id = invoice_items_data.get('invoice_id')
        invoice_items_vo.redeemable = invoice_items_data.get('redeemable')
        invoice_items_vo.unit_price = invoice_items_data.get('unit_price')
        invoice_items_vo.batch_batch = invoice_items_data.get('batch_batch')
        invoice_items_vo.description = invoice_items_data.get('description')
        invoice_items_vo.fixed_price = invoice_items_data.get('fixed_price')
        invoice_items_vo.no_discount = invoice_items_data.get('no_discount')
        invoice_items_vo.precautions = invoice_items_data.get('precautions')
        invoice_items_vo.redemptions = invoice_items_data.get('redemptions')
        invoice_items_vo.track_stock = invoice_items_data.get('track_stock')
        invoice_items_vo.batch_expiry = invoice_items_data.get('batch_expiry')
        invoice_items_vo.facility_ref = invoice_items_data.get('facility_ref')
        invoice_items_vo.facility_paid = invoice_items_data.get(
            'facility_paid')
        invoice_items_vo.selling_price = invoice_items_data.get(
            'selling_price')
        invoice_items_vo.last_edited_by = invoice_items_data.get(
            'last_edited_by')
        invoice_items_vo.facility_status = invoice_items_data.get(
            'facility_status')
        invoice_items_vo.package_original_price = invoice_items_data.get(
            'package_original_price')
        invoice_items_vo.expiry_after_dispensing = invoice_items_data.get(
            'expiry_after_dispensing')
        if is_update:
            data = InvoiceItemDAO.get_data(session, invoice_item_id,
                                           invoices_id)
            if data:
                invoice_items_vo.id = data.id
                InvoiceItemDAO.update(invoice_items_vo, session)
            else:
                InvoiceItemDAO.insert_invoices_item(invoice_items_vo, session)
        else:
            InvoiceItemDAO.insert_invoices_item(invoice_items_vo, session)
        return True
    except Exception as e:
        logger.error("Function patient_insert_db got error = {}".format(e))
        return False


def update_timestamp(scheduler_id, session, current_time):
    logger.info("Function: update_timestamp")
    logger.info(
        "Params: scheduler_id = {}, session = {}, current_time ={}".format(
            scheduler_id, session, current_time))
    try:
        update_vo = SchedulerVO()
        if scheduler_id:
            update_vo.id = scheduler_id
            update_vo.timestamp = current_time
            update_vo.scheduler_name = SCHEDULER_NAME
            SchedulerDAO.update(update_vo, session)
        else:
            update_vo.timestamp = current_time
            update_vo.scheduler_name = SCHEDULER_NAME
            SchedulerDAO.insert_scheduler(update_vo, session)
        return True

    except Exception as e:
        logger.error("Function update_timestamp got error = {}".format(e))
        return False


# context = "function:dev"
# event = {}
# response_payload = lambda_handler(event, context)
# print(response_payload)
