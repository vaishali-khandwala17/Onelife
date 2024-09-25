import logging
from configparser import ConfigParser
from config import db_connection
from services import AppServices
from models import Base, DrugDetailsVO, InvoicesVO
from dao import DrugDetailsDAO, InvoicesDAO, InvoicesItemDAO

logger = logging.getLogger("ksi_plato_invoice_drug_operations")
logger.setLevel(logging.INFO)

configure = ConfigParser()
configure.read('config.ini')

ERROR_FORMAT = configure.get('ERROR_HANDLING', 'format')
PROCESS_COMPLETE_STATUS = configure.get('GENERAL_CONFIG', 'process_complete')

NURSING_HOME_CODE = configure.get('STATIC_PARAMS', 'nursing_home_code')
ROOM_NUMBER = configure.get('STATIC_PARAMS', 'room_number')
BED_NUMBER = configure.get('STATIC_PARAMS', 'bed_number')
WARD_NUMBER = configure.get('STATIC_PARAMS', 'word_number')

PATIENT_ID_LENGTH = int(configure.get('ON_CUBE_INTERFACE_SIZE', 'patient_id'))
RX_NUMBER_LENGTH = int(configure.get('ON_CUBE_INTERFACE_SIZE', 'rx_number'))
QUANTITY_LENGTH = int(configure.get('ON_CUBE_INTERFACE_SIZE', 'quantity'))
DRUG_ID_LENGTH = int(configure.get('ON_CUBE_INTERFACE_SIZE', 'drug_id'))
START_DATE_LENGTH = int(configure.get('ON_CUBE_INTERFACE_SIZE', 'start_date'))
STOP_DATE_LENGTH = int(configure.get('ON_CUBE_INTERFACE_SIZE', 'stop_date'))
ADMIN_TIME_LENGTH = int(configure.get('ON_CUBE_INTERFACE_SIZE', 'admin_time'))
RANDOM_1_LENGTH = int(configure.get('ON_CUBE_INTERFACE_SIZE', 'random_1'))
RANDOM_2_LENGTH = int(configure.get('ON_CUBE_INTERFACE_SIZE', 'random_2'))
RANDOM_3_LENGTH = int(configure.get('ON_CUBE_INTERFACE_SIZE', 'random_3'))
RANDOM_4_LENGTH = int(configure.get('ON_CUBE_INTERFACE_SIZE', 'random_4'))
RANDOM_5_LENGTH = int(configure.get('ON_CUBE_INTERFACE_SIZE', 'random_5'))
BED_NUMBER_LENGTH = int(configure.get('ON_CUBE_INTERFACE_SIZE', 'bed_number'))
ROOM_NUMBER_LENGTH = int(configure.get('ON_CUBE_INTERFACE_SIZE',
                                       'room_number'))
WARD_NUMBER_LENGTH = int(configure.get('ON_CUBE_INTERFACE_SIZE',
                                       'ward_number'))
BATCH_NUMBER_LENGTH = int(configure.get('ON_CUBE_INTERFACE_SIZE',
                                        'batch_number'))
PATIENT_NAME_LENGTH = int(configure.get('ON_CUBE_INTERFACE_SIZE',
                                        'patient_name'))
RX_DATE_TIME_LENGTH = int(configure.get('ON_CUBE_INTERFACE_SIZE',
                                        'rx_date_time'))
ADMIN_DESCRIPTION_LENGTH = int(configure.get('ON_CUBE_INTERFACE_SIZE',
                                             'admin_description'))
NURSING_HOME_CODE_LENGTH = int(configure.get('ON_CUBE_INTERFACE_SIZE',
                                             'nursing_home_code'))


def validate_request(request_data):
    logger.info("Function validate_request")
    logger.info("params: request_data = {}".format(request_data))
    attributes = ["invoices_id", "invoice_item_data"]
    request_data_keys = request_data.keys()
    for attribute in attributes:
        if attribute in request_data_keys and request_data[attribute]:
            pass
        else:
            return False, attribute
    return True, ""


def lambda_handler(event, context):
    logger.info("Params: event = {}".format(event))
    logger.info("Params: context = {}".format(context))

    server_alias = AppServices.get_env(context)
    logger.info("got env = {}".format(server_alias))

    db_engine, session = db_connection(server_alias)
    Base.metadata.create_all(db_engine)

    is_valid, attribute = validate_request(event)

    if not is_valid:
        message = "{} parameter missing or invalid.".format(attribute)
        response_payload = AppServices.app_response(400, message, False, {})
        return response_payload

    response_payload = main_handler(event, session)
    logger.info("Final response = {}".format(response_payload))
    return response_payload


def main_handler(request_data, session):
    logger.info("Function: main_handler")
    logger.info("request_data = {}".format(request_data))
    try:
        invoices_id = request_data["invoices_id"]

        is_generate, response_payload = file_generate_handler(request_data,
                                                              session)
        if not is_generate:
            return response_payload

        is_update = update_invoices_status(session, invoices_id)
        logger.info("invoice update status = {}".format(is_update))

        if not is_update:
            message = "something went wrong!!"
            response_payload = AppServices.app_response(500, message, False,
                                                        {})
            return response_payload

        return response_payload

    except Exception as e:
        logger.error(ERROR_FORMAT.format(e.__str__()))
        message = "something went wrong!!"
        response_payload = AppServices.app_response(500, message, False, {})
        return response_payload


def file_generate_handler(request_data, session):
    logger.info("Function: file_generate_handler")
    logger.info("Params: request_data = {}".format(request_data))
    try:
        invoices_id = request_data["invoices_id"]
        invoice_item_drug_data_list = request_data["invoice_item_data"]
        logger.info("invoices_id = {}".format(invoices_id))
        data = InvoicesDAO.get_data(session, invoices_id)
        logger.info("Data = {}".format(data))
        if not data:
            logger.info("invoice data not found by invoice id")
            message = "Data not found!!"
            response_payload = AppServices.app_response(404, message, False,
                                                        {})
            return False, response_payload

        invoice_data_dict = data[0].to_dict()
        patient_data_dict = data[1].to_dict()

        final_content = ""

        for drug_data in invoice_item_drug_data_list:
            if "batch" in drug_data:
                batch_number = drug_data["batch"][0: BATCH_NUMBER_LENGTH]
            else:
                batch_number = invoice_data_dict["invoices_batch"]
            drug_data["batch"] = batch_number[0: BATCH_NUMBER_LENGTH]
            is_success = insert_drug_data(drug_data, session)
            if not is_success:
                logger.info("drug data insert fail!!")
                message = "something went wrong!!"
                response_payload = AppServices.app_response(500, message,
                                                            False,
                                                            {})
                return response_payload
            invoice_item_data = InvoicesItemDAO.get_data(session,
                                                         drug_data[
                                                             "invoice_item_id"]).to_dict()

            file_content = ""
            nursing_home_code = NURSING_HOME_CODE[0:NURSING_HOME_CODE_LENGTH]
            room_number = ROOM_NUMBER[0:ROOM_NUMBER_LENGTH]
            bed_number = BED_NUMBER[0:BED_NUMBER_LENGTH]
            ward_number = WARD_NUMBER[0:WARD_NUMBER_LENGTH]
            rx_number = invoice_item_data["invoice_item_id"][
                        0:RX_NUMBER_LENGTH]
            rx_date_time = invoice_data_dict["created_on"][
                           0:RX_DATE_TIME_LENGTH]
            quantity = drug_data["qty"][0:QUANTITY_LENGTH]
            random_1 = drug_data["random_1"][0:RANDOM_1_LENGTH]
            random_2 = drug_data["random_2"][0:RANDOM_2_LENGTH]
            random_3 = drug_data["random_3"][0:RANDOM_3_LENGTH]
            random_4 = drug_data["random_4"][0:RANDOM_4_LENGTH]
            random_5 = drug_data["random_5"][0:RANDOM_5_LENGTH]
            drug_id = drug_data["drug_id"][0:DRUG_ID_LENGTH]
            start_date = drug_data["start_date"][0:START_DATE_LENGTH]
            stop_date = drug_data["end_date"][0:STOP_DATE_LENGTH]
            admin_time = drug_data["admin_time"][0:ADMIN_DESCRIPTION_LENGTH]
            admin_description = drug_data["admin_description"][
                                0:ADMIN_DESCRIPTION_LENGTH]

            patient_id = patient_data_dict["patient_id"][0:PATIENT_ID_LENGTH]
            patient_name = patient_data_dict["patient_name"][
                           0:PATIENT_NAME_LENGTH]

            logger.info("nursing_home_code = {}, room_number = {}, bed_number "
                        "= {}, ward_number = {}, rx_number = {}, rx_date_time "
                        "= {}, random_1 = {}, random_2 = {}, random_3 = {}, "
                        "random_4 = {}, random_5 = {}, quantity = {}, drug_id "
                        "= {}, start_date = {}, stop_date = {}, admin_time = "
                        "{}, admin_description = {}, batch_number = {}, "
                        "patient_id = {}, patient_name = {}"
                        .format(nursing_home_code, room_number, bed_number,
                                ward_number, rx_number, rx_date_time, random_1,
                                random_2, random_3, random_4, random_5,
                                quantity, drug_id, start_date, stop_date,
                                admin_time, admin_description, batch_number,
                                patient_id, patient_name))

            length_list = [PATIENT_NAME_LENGTH, PATIENT_ID_LENGTH,
                           NURSING_HOME_CODE_LENGTH, ROOM_NUMBER_LENGTH,
                           BED_NUMBER_LENGTH, WARD_NUMBER_LENGTH,
                           RX_NUMBER_LENGTH, RX_DATE_TIME_LENGTH,
                           QUANTITY_LENGTH, DRUG_ID_LENGTH, START_DATE_LENGTH,
                           STOP_DATE_LENGTH, ADMIN_TIME_LENGTH,
                           ADMIN_DESCRIPTION_LENGTH, RANDOM_1_LENGTH,
                           RANDOM_2_LENGTH, RANDOM_3_LENGTH, RANDOM_4_LENGTH,
                           RANDOM_5_LENGTH, BATCH_NUMBER_LENGTH]
            character_list = [patient_name, patient_id, nursing_home_code,
                              room_number, bed_number, ward_number, rx_number,
                              rx_date_time, quantity, drug_id, start_date,
                              stop_date, admin_time, admin_description,
                              random_1, random_2, random_3, random_4, random_5,
                              batch_number]

            for content_char in range(len(character_list)):
                file_content += '{}{}'.format(character_list[content_char],
                                              " " * (length_list[content_char]
                                                     - len(
                                                          character_list[
                                                              content_char])))
            final_content += file_content
            final_content += "\n"

        response = {
            "statusCode": 200,
            "body": final_content.encode('utf-8'),
            "headers": {
                "Content-Type": "text/plain",
                "Content-Disposition": "attachment; filename={}-{}.txt".format(
                    patient_data_dict["patient_id"],
                    invoice_data_dict["invoice"])
            }
        }
        return True, response

    except Exception as e:
        logger.error(ERROR_FORMAT.format(e.__str__()))
        message = "something went wrong!!"
        response_payload = AppServices.app_response(500, message, False, {})
        return False, response_payload


def update_invoices_status(session, invoices_id):
    logger.info("Function: update_invoices_status")
    logger.info("Params: invoices_id = {}".format(invoices_id))
    try:
        invoice_update_vo = InvoicesVO()
        invoice_update_vo.id = invoices_id
        invoice_update_vo.invoice_status = PROCESS_COMPLETE_STATUS
        InvoicesDAO.update(invoice_update_vo, session)
        return True

    except Exception as e:
        logger.error(
            "Function update_invoices_status got error = {}".format(e))
        return False


def insert_drug_data(request_data, session):
    logger.info("Function: insert_drug_data")
    logger.info("Params: request_data = {}".format(request_data))
    try:
        logger.info("request_data= {}".format(request_data))
        logger.info("type = {}".format(type(request_data)))
        drug_details_vo = DrugDetailsVO()
        drug_details_vo.invoices_item_id = request_data["invoice_item_id"]
        drug_details_vo.drug_id = request_data["drug_id"]
        drug_details_vo.qty = request_data["qty"]
        drug_details_vo.start_date = request_data["start_date"]
        drug_details_vo.end_date = request_data["end_date"]
        drug_details_vo.admin_time = request_data["admin_time"]
        drug_details_vo.batch = request_data["batch"]
        drug_details_vo.admin_description = request_data["admin_description"]
        drug_details_vo.random_1 = request_data["random_1"]
        drug_details_vo.random_2 = request_data["random_2"]
        drug_details_vo.random_3 = request_data["random_3"]
        drug_details_vo.random_4 = request_data["random_4"]
        drug_details_vo.random_5 = request_data["random_5"]
        DrugDetailsDAO.insert_drug_detail(drug_details_vo, session)
        return True
    except Exception as e:
        logger.error(ERROR_FORMAT.format(e.__str__()))
        return False


# context = "function:dev"
# event = {
#     "invoices_id": 1,
#     "invoice_item_data": [
#         {
#             "invoice_item_id": "1",
#             "drug_id": "G1234567H",
#             "qty": "2",
#             "start_date": "220122",
#             "end_date": "230523",
#             "admin_time": "10:00:00",
#             "batch": "123",
#             "admin_description": "bb",
#             "random_1": "random_1",
#             "random_2": "random_2",
#             "random_3": "random_3",
#             "random_4": "random_4",
#             "random_5": "random_5"
#         },
#         {
#             "invoice_item_id": "1",
#             "drug_id": "G1234567H",
#             "qty": "2",
#             "start_date": "220122",
#             "end_date": "230523",
#             "admin_time": "10:00:00",
#             "admin_description": "bb",
#             "random_1": "random_1",
#             "random_2": "random_2",
#             "random_3": "random_3",
#             "random_4": "random_4",
#             "random_5": "random_5"
#         }
#     ]
# }
#
# response_payload = lambda_handler(event, context)
# print(response_payload)
