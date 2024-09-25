import logging
from configparser import ConfigParser

import requests

from config import db_connection
from dao import InvoicesDAO, InvoicesItemDAO, PatientDAO, DrugDetailsDAO
from models import Base, InvoicesVO, PatientVO
from services import AppServices

logger = logging.getLogger("ksi_plato_invoice_operations")
logger.setLevel(logging.INFO)

configure = ConfigParser()
configure.read('config.ini')

ERROR_FORMAT = configure.get('ERROR_HANDLING', 'format')
NURSING_HOME_CODE = configure.get('STATIC_PARAMS', 'nursing_home_code')
ROOM_NUMBER = configure.get('STATIC_PARAMS', 'room_number')
BED_NUMBER = configure.get('STATIC_PARAMS', 'bed_number')
WORD_NUMBER = configure.get('STATIC_PARAMS', 'word_number')
PRESCRIPTION_FILTER = configure.get('GENERAL_CONFIG', 'prescription_filter')
PROCESS_STATUS = configure.get('GENERAL_CONFIG', 'process_status')
API_URL = configure.get('DEV_PLATO_API', 'api_url')
PATIENT_VIEW_URL = configure.get('DEV_PLATO_API', 'patient_view_url')
API_TOKEN = configure.get('DEV_PLATO_API', 'api_token')
DEFAULT_INVOICE_STATUS = configure.get('GENERAL_CONFIG',
                                       'default_invoice_status')


def lambda_handler(event, context):
    logger.info("Params: event = {}".format(event))
    logger.info("Params: context = {}".format(context))

    server_alias = AppServices.get_env(context)
    logger.info("got env = {}".format(server_alias))

    db_engine, session = db_connection(server_alias)
    Base.metadata.create_all(db_engine)

    response_payload = patient_invoices(session, event)
    logger.info("final response = {}".format(response_payload))
    return response_payload


def get_invoices_data(session, invoices_id, invoices_data):
    invoices_data_dict = invoices_data[0].to_dict()
    patient_data = invoices_data[1].to_dict()
    if invoices_data_dict["invoice_status"] == DEFAULT_INVOICE_STATUS:
        is_update = update_invoices_status(session, invoices_id)
        logger.info("invoices update status = {}".format(is_update))
        if not is_update:
            message = "Something went wrong!!"
            response_payload = AppServices.app_response(500, message,
                                                        False, {})
            return response_payload
    invoices_data_dict["invoice_status"] = PROCESS_STATUS
    extra_invoices_data = {
        "nursing_home_code": NURSING_HOME_CODE,
        "room_number": ROOM_NUMBER,
        "bed_number": BED_NUMBER,
        "word_number": WORD_NUMBER
    }

    invoices_data_dict.update(extra_invoices_data)
    invoices_data_dict.update(patient_data)
    invoices_item_data = InvoicesItemDAO.get_data(session,
                                                  invoices_id)
    prescription = []
    if invoices_item_data:
        for invoices_item in invoices_item_data:
            if invoices_item.category == PRESCRIPTION_FILTER:
                invoices_item_dict = invoices_item.to_dict()
                drug_details = DrugDetailsDAO.get_data(session,
                                                       invoices_item_dict[
                                                           "id"])
                if drug_details:
                    invoices_item_dict.update(drug_details.to_dict())
                else:
                    invoices_item_dict["drug_id"] = ""
                    invoices_item_dict["start_date"] = ""
                    invoices_item_dict["end_date"] = ""
                    invoices_item_dict["admin_time"] = ""
                    invoices_item_dict["batch"] = ""
                    invoices_item_dict["admin_description"] = ""

                prescription.append(invoices_item_dict)
    invoices_data_dict["prescription"] = prescription
    logger.info("final invoices data = {}".format(invoices_data))
    message = "patient invoice found."
    response_payload = AppServices.app_response(200, message,
                                                True,
                                                invoices_data_dict)
    return response_payload


def patient_invoices(session, request_data):
    logger.info("function:patient_invoices")
    logger.info("Params: request_data = {}".format(request_data))
    try:
        if 'invoices_id' in request_data and request_data['invoices_id']:
            invoices_id = request_data['invoices_id']
            invoices_data = InvoicesDAO.get_data(session, invoices_id)
            if invoices_data:
                response_payload = get_invoices_data(session, invoices_id,
                                                     invoices_data)
                return response_payload
            else:
                invoices_data = InvoicesDAO.get_one_data(session, invoices_id)
                if not invoices_data:
                    message = "Data not found!!"
                    response_payload = AppServices.app_response(404, message,
                                                                True,
                                                                {})
                    return response_payload
                invoices_data_dict = invoices_data.to_dict()
                patient_id = invoices_data_dict["patient_id"]
                logger.info("Params: patient_id = {}".format(patient_id))
                api_call = '{}'.format(
                    API_URL + PATIENT_VIEW_URL + f"{patient_id}")
                headers = {'Authorization': "Bearer {}".format(API_TOKEN)}
                api_response = requests.get(api_call, headers=headers).json()
                logger.info(
                    "Plato fetch api response = {}".format(api_response))
                if not api_response:
                    message = "Data not found!!"
                    response_payload = AppServices.app_response(404, message,
                                                                True,
                                                                {})
                    return response_payload
                for patient_data in api_response:
                    is_true = patient_insert_db(patient_data, session)
                    logger.info("NEW patient data insert = {}".format(is_true))
                invoices_data = InvoicesDAO.get_data(session, invoices_id)

                if invoices_data:
                    response_payload = get_invoices_data(session, invoices_id,
                                                         invoices_data)
                    return response_payload

                message = "Data not found!!"
                response_payload = AppServices.app_response(404, message,
                                                            True, {})
                return response_payload
        else:
            message = "invoices_id parameter is missing or invalid."
            response_payload = AppServices.app_response(400, message, False,
                                                        {})
            return response_payload

    except Exception as e:
        logger.error(ERROR_FORMAT.format(e.__str__(), "invoice_view"))
        message = "Something went wrong!!"
        response_payload = AppServices.app_response(500, message, False, {})
        return response_payload


def patient_insert_db(patient_data, session):
    logger.info("Function: patient_insert_db")
    logger.info("Param: patient_data = {}".format(patient_data))
    try:
        patient_vo = PatientVO()
        if patient_data.get('dob') != '0000-00-00':
            patient_vo.dob = patient_data.get('dob')
        patient_vo.given_id = patient_data.get('given_id')
        patient_vo.name = patient_data.get('name')
        patient_vo.nric = patient_data.get('nric')
        patient_vo.marital_status = patient_data.get('marital_status')
        patient_vo.sex = patient_data.get('sex')
        patient_vo.nationality = patient_data.get('nationality')
        patient_vo.allergies_select = patient_data.get('allergies_select')
        patient_vo.allergies = patient_data.get('allergies')
        patient_vo.nric_type = patient_data.get('nric_type')
        patient_vo.food_allergies_select = patient_data.get(
            'food_allergies_select')
        patient_vo.food_allergies = patient_data.get('food_allergies')
        patient_vo.g6pd = patient_data.get('g6pd')
        patient_vo.dial_code = patient_data.get('dial_code', "")
        patient_vo.telephone = patient_data.get('telephone')
        patient_vo.alerts = patient_data.get('alerts')
        patient_vo.address = patient_data.get('address')
        patient_vo.postal = patient_data.get('postal')
        patient_vo.email = patient_data.get('email')
        patient_vo.telephone2 = patient_data.get('telephone2')
        patient_vo.telephone3 = patient_data.get('telephone3')
        patient_vo.title = patient_data.get('title')
        patient_vo.dnd = patient_data.get('dnd')
        patient_vo.occupation = patient_data.get('occupation')
        patient_vo.doctor = patient_data.get('doctor')
        patient_vo.created_on = patient_data.get('created_on')
        patient_vo.created_by = patient_data.get('created_by')
        patient_vo.last_edited = patient_data.get('last_edited')
        patient_vo.last_edited_by = patient_data.get('last_edited_by')
        patient_vo.notes = patient_data.get('notes')
        patient_vo.referred_by = patient_data.get('referred_by')
        patient_vo.plato_id = patient_data.get('_id')
        PatientDAO.insert_patient(patient_vo, session)
        return True
    except Exception as e:
        logger.error("Function patient_insert_db got error = {}".format(e))
    return False


def update_invoices_status(session, invoices_id):
    logger.info("Function: update_invoices_status")
    logger.info("Params: invoices_id = {}".format(invoices_id))
    try:
        invoice_update_vo = InvoicesVO()
        invoice_update_vo.id = invoices_id
        invoice_update_vo.invoice_status = PROCESS_STATUS
        InvoicesDAO.update(invoice_update_vo, session)
        return True

    except Exception as e:
        logger.error(
            "Function update_invoices_status got error = {}".format(e))
        return False


# context = "function:dev"
# event = {
#     'invoices_id': 49
# }
# response_payload = lambda_handler(event, context)
# print("response_payload", response_payload)
