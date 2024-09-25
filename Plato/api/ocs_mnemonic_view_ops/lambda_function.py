import logging
from configparser import ConfigParser
from config import db_connection
from dao import MnemonicDAO
from models import Base
from services import AppServices

logger = logging.getLogger("ocs_Mnemonic_operations")
logger.setLevel(logging.INFO)

configure = ConfigParser()
configure.read('config.ini')

ERROR_FORMAT = configure.get('ERROR_HANDLING', 'format')


def lambda_handler(event, context):
    logger.info("Params: event = {}".format(event))
    logger.info("Params: context = {}".format(context))

    server_alias = AppServices.get_env(context)
    logger.info("got env = {}".format(server_alias))

    db_engine, session = db_connection(server_alias)
    Base.metadata.create_all(db_engine)

    response_payload = get_mnemonic_details(session, event)
    logger.info("final response = {}".format(response_payload))
    return response_payload


def get_mnemonic_details(session, request_data):
    logger.info("Function: get_mnemonic_details")
    logger.info("Params: request_data = {}".format(request_data))
    try:
        if "search_value" in request_data:
            search_value = request_data["search_value"]
            mnemonic_data_response = MnemonicDAO.get_data(session,
                                                          search_value)
        else:
            mnemonic_data_response = MnemonicDAO.get_data(session, None)
        if not mnemonic_data_response:
            message = "Data not found!!"
            response_payload = AppServices.app_response(404, message, False,
                                                        {})
            return response_payload
        mnemonic_data_list = []
        for mnemonic_data in mnemonic_data_response:
            mnemonic_data_list.append(mnemonic_data.to_dict())
        message = "Mnemonic Data found!!"
        response_payload = AppServices.app_response(200, message, True,
                                                    mnemonic_data_list)
        return response_payload

    except Exception as e:
        logger.info("Function get_mnemonic_details got error = {}".format(e))
        message = "Something went wrong!!"
        response_payload = AppServices.app_response(500, message, False, {})
        return response_payload

# context = "function:dev"
# event = {
#     'search_value': "ZOCOR 10MG TAB"
# }
# response_payload = lambda_handler(event, context)
# print("response_payload", response_payload)
