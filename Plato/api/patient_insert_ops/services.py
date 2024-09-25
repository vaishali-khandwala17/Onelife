import configparser
import json
import logging

import requests

configure = configparser.ConfigParser()
configure.read('config.ini')

API_URL = configure.get('DEV_PLATO_API', 'api_url')
PATIENT_POST_URL = configure.get('DEV_PLATO_API', 'patient_post_url')
API_TOKEN = configure.get('DEV_PLATO_API', 'api_token')
logger = logging.getLogger("ksi_plato_patient_operations")
logger.setLevel(logging.INFO)

ERROR_FORMAT = configure.get('ERROR_HANDLING', 'format')


class AppServices:

    def __init__(self):
        self.region_name = "us-east-2"

    @staticmethod
    def get_env(context):
        split_arn = context.invoked_function_arn.split(':')
        # split_arn = context.split(':')
        env = split_arn[len(split_arn) - 1]
        env_list = ['dev', 'qa', 'prod']
        return env if env in env_list else 'dev'

    @staticmethod
    def app_response(status_code: int, message: str, success: bool = None,
                     data: any = None) -> dict:
        response = {
            "status_code": status_code,
            "success": success,
            "message": message,
            "data": data
        }

        return response


class PlatoServices:
    @staticmethod
    def patient_post_api(data_dict):
        plato_id = None
        logger.info("Function: patient_post_api")
        print("Param: data_dict{}".format(data_dict))
        response = {}

        try:
            headers = {'Authorization': "Bearer {}".format(API_TOKEN)}
            data_dict = json.dumps(data_dict)
            api_response = requests.post(
                '{}{}'.format(API_URL, PATIENT_POST_URL),
                data=data_dict, headers=headers)
            response_text = api_response.text
            response_status_code = api_response.status_code
            print("response_text", response_text)
            print(type(response_text))
            res = json.loads(response_text)

            if response_status_code == 201 and "_id" in res:
                plato_id = res.get('_id')
                print("plato_id", plato_id)

            response.update({
                "status_code": 200,
                "success": True,
                "message": "insert successful",
                "data": {}
            })

            return plato_id

        except Exception as patient_post_api_exec:
            logger.error(ERROR_FORMAT.format(patient_post_api_exec.__str__(),
                                             "patient_post_api"))

            response.update({
                "status_code": 500,
                "success": False,
                "message": "something went wrong",
                "data": {}
            })

        return response
