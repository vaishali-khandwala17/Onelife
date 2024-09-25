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
PATIENT_INVOICE_URL = configure.get('DEV_PLATO_API', 'patient_invoice_url')
API_TOKEN = configure.get('DEV_PLATO_API', 'api_token')


def lambda_handler(event, context):
    logger.info("got event = {}".format(event))
    logger.info("got context = {}".format(context))
    server_alias = AppServices.get_env(context)
    logger.info("got env = {}".format(server_alias))
    response_payload = plato_invoice_api(event)
    logger.info("final response = {}".format(response_payload))
    return response_payload


def plato_invoice_api(event):
    logger.info("Function: plato_invoice_api")
    # response = {}
    try:
        if "patient_id" in event and event['patient_id']:
            patient_id = event.get("patient_id")
            logger.info("Params: patient_id = {}".format(patient_id))
            api_call = '{}{}{}'.format(API_URL, PATIENT_INVOICE_URL,
                                       patient_id)
            headers = {'Authorization': "Bearer {}".format(API_TOKEN)}
            api_response = requests.get(api_call, headers=headers).json()
            logger.info("Invoice Api Response = {}".format(api_response))
            if api_response:
                api_response = api_response[0]
                message = "patient invoice found successfully."
                response_payload = AppServices.app_response(200, message,
                                                            True,
                                                            api_response)
            else:
                message = "patient invoice data not found."
                response_payload = AppServices.app_response(404, message,
                                                            True,
                                                            {})

        else:
            message = "patient id parameter required, not found."
            response_payload = AppServices.app_response(400, message,
                                                        False,
                                                        {})


    except Exception as patient_invoice_exec:
        logger.error(ERROR_FORMAT.format(patient_invoice_exec.__str__(),
                                         "plato_invoice_api"))
        message = "something went wrong"
        response_payload = AppServices.app_response(500, message,
                                                    False,
                                                    {})

    return response_payload

# context = "function:dev"
# event = {
#     'patient_id': 'ccc3d572558b440f868d3efac0484c09'
# }
# event = {}
# response_payload = lambda_handler(event, context)
# print(response_payload)
