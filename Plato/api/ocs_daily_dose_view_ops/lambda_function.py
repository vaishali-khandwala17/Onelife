import logging
from configparser import ConfigParser
from config import db_connection
from dao import DailyDoseMasterDAO
from models import Base
from services import AppServices

logger = logging.getLogger("ocs_daily_dose_operations")
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

    response_payload = get_daily_dose_details(session, event)
    logger.info("final response = {}".format(response_payload))
    return response_payload


def get_daily_dose_details(session, request_data):
    logger.info("Function: get_daily_dose_details")
    logger.info("Params: request_data = {}".format(request_data))
    try:
        if "search_value" in request_data:
            search_value = request_data["search_value"]
            daily_dose_response = DailyDoseMasterDAO.get_data(session,
                                                              search_value)
        else:
            daily_dose_response = DailyDoseMasterDAO.get_data(session, None)
        if not daily_dose_response:
            message = "Data not found!!"
            response_payload = AppServices.app_response(404, message, False,
                                                        {})
            return response_payload
        daily_dose_data_list = []
        for daily_dose_data in daily_dose_response:
            daily_dose_data_list.append(daily_dose_data.to_dict())
        message = "Daily dose Data found!!"
        response_payload = AppServices.app_response(200, message, True,
                                                    daily_dose_data_list)
        return response_payload

    except Exception as e:
        logger.info("Function get_daily_dose_details got error = {}".format(e))
        message = "Something went wrong!!"
        response_payload = AppServices.app_response(500, message, False, {})
        return response_payload


# context = "function:dev"
# event = {
#     # 'search_value': "Q24H"
# }
# response_payload = lambda_handler(event, context)
# print("response_payload", response_payload)
