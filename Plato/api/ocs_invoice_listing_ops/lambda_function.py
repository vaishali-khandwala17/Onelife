import logging
from configparser import ConfigParser
from config import db_connection
from services import AppServices
from dao import InvoicesDAO
from models import Base

logger = logging.getLogger("ksi_plato_invoice_listing_operations")
logger.setLevel(logging.INFO)

configure = ConfigParser()
configure.read('config.ini')

ERROR_FORMAT = configure.get('ERROR_HANDLING', 'format')
PRESCRIPTION_FILTER = configure.get('GENERAL_CONFIG', 'prescription_filter')


def validate_request(request_data):
    logger.info("Function validate_request")
    logger.info("params: request_data = {}".format(request_data))
    attributes = ["page_number", "page_size"]
    request_data_keys = request_data.keys()
    for attribute in attributes:
        if attribute in request_data_keys and request_data[attribute]:
            pass
        else:
            return False, attribute
    return True, ""


def lambda_handler(event, context):
    logger.info("got event = {}".format(event))
    logger.info("got context = {}".format(context))

    server_alias = AppServices.get_env(context)
    logger.info("got env = {}".format(server_alias))

    db_engine, session = db_connection(server_alias)
    Base.metadata.create_all(db_engine)

    is_valid, attribute = validate_request(event)

    if not is_valid:
        message = "{} parameter missing or invalid.".format(attribute)
        response_payload = AppServices.app_response(400, message, False,
                                                    {})
        return response_payload

    response_payload = get_invoice_data(session, event)
    logger.info("Final response_payload = {}".format(response_payload))
    return response_payload


def get_invoice_data(session, request_data):
    logger.info("Function: get_invoice_data")
    logger.info("Params: request_data = {}".format(request_data))
    data_dict_list = []
    try:
        page_number = int(request_data["page_number"])
        limit = int(request_data["page_size"])
        patient_id_filter = request_data.get("patient_id", "")
        invoice_filter = request_data.get("invoice_number", "")
        medicine_filter = bool(request_data.get("medicine_filter", ""))
        if medicine_filter:
            prescription_filter = PRESCRIPTION_FILTER
        else:
            prescription_filter = ""

        skip = (page_number - 1) * limit

        data_list = InvoicesDAO.get_data(session, skip, limit,
                                         patient_id_filter, invoice_filter,
                                         prescription_filter)
        if not data_list:
            message = "Data not found!!"
            response_payload = AppServices.app_response(404, message, False,
                                                        [])
            return response_payload

        for invoices_data in data_list:
            data_dict = invoices_data[0].to_dict()
            data_dict.update(invoices_data[1].to_dict())
            data_dict_list.append(data_dict)
        logger.info("data_dict_list = {}".format(data_dict_list))
        message = "Invoice data found!!"
        response_payload = AppServices.app_response(200, message, True,
                                                    data_dict_list)
        return response_payload
    except Exception as e:
        logger.info("Function: get_invoice_data got error = {}".format(e))
        message = "Something went wrong!!"
        response_payload = AppServices.app_response(500, message, False, [])
        return response_payload


# context = "function:dev"
# event = {"page_number": 1, "page_size": 10}
# response_payload = lambda_handler(event, context)
# print(response_payload)
