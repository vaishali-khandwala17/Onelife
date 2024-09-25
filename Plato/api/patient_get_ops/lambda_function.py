import logging
from configparser import ConfigParser

import requests

from services import AppServices

logger = logging.getLogger("ksi_plato_patient_operations")
logger.setLevel(logging.INFO)

configure = ConfigParser()
configure.read('config.ini')

ERROR_FORMAT = configure.get('ERROR_HANDLING', 'format')
API_URL = configure.get('DEV_PLATO_API', 'api_url')
PATIENT_VIEW_URL = configure.get('DEV_PLATO_API', 'patient_view_url')
API_TOKEN = configure.get('DEV_PLATO_API', 'api_token')


def lambda_handler(event, context):
    logger.info("got event = {}".format(event))
    logger.info("got context = {}".format(context))
    server_alias = AppServices.get_env(context)
    logger.info("got env = {}".format(server_alias))
    response_payload = plato_fetch_api(event)
    logger.info("Final response = {}".format(response_payload))
    return response_payload


def plato_fetch_api(event):
    logger.info("Function: plato_fetch_api")
    # response = {}
    try:
        if "patient_id" in event and event['patient_id']:
            patient_id = event.get("patient_id")
            logger.info("Params: patient_id = {}".format(patient_id))
            api_call = '{}'.format(API_URL + PATIENT_VIEW_URL + f"{patient_id}"
                                   )
            headers = {'Authorization': "Bearer {}".format(API_TOKEN)}
            api_response = requests.get(api_call, headers=headers).json()
            logger.info("Plato fetch api response = {}".format(api_response))

            if api_response:
                api_response = api_response[0]
                message = "patient data found successfully."
                response = AppServices.app_response(200, message,
                                                    True,
                                                    api_response)
            else:
                message = "patient data not found for given patient_id"
                response = AppServices.app_response(404, message,
                                                    True,
                                                    {})

        else:
            message = "patient id parameter required, not found"
            response = AppServices.app_response(400, message,
                                                False,
                                                {})

    except Exception as patient_view_exec:
        logger.error(ERROR_FORMAT.format(patient_view_exec.__str__(),
                                         "plato_fetch_api"))
        message = "something went wrong"
        response = AppServices.app_response(500, message, False, {})

    return response


# context = "function:dev"
# event = {
#     'patient_id': '4c829396a38a4fcfe22362e17442b190'
# }

# event = {}
# response_payload = lambda_handler(event, context)
# print(response_payload)
