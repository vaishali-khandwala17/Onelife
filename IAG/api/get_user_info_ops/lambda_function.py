import json
import logging
from configparser import ConfigParser
import boto3
from config import db_connection
from dao import UserDetailsDAO
from models import Base
from services import AppServices

logger = logging.getLogger("ksi_login_verify_operations")
logger.setLevel(logging.INFO)

configure = ConfigParser()
configure.read('config.ini')

cognito_client = boto3.client('cognito-idp')

ERROR_FORMAT = configure.get('ERROR_HANDLING', 'format')

USER_POOL_ID = configure.get('COGNITO_CONFIG', 'user_pool_id')
CLIENT_ID = configure.get('COGNITO_CONFIG', 'client_id')
CLIENT_SECRET = configure.get('COGNITO_CONFIG', 'client_secret')


def lambda_handler(event, context):
    logger.info("Params: event = {}".format(event))
    logger.info("Params: context = {}".format(context))

    server_alias = AppServices.get_env(context)
    logger.info("got env = {}".format(server_alias))

    db_engine, session = db_connection(server_alias)
    Base.metadata.create_all(db_engine)

    response_payload = get_user_data(event, session)
    logger.info("final response_payload = {}".format(response_payload))
    return response_payload


def get_user_data(request_data, session):
    logger.info("Function: get_user_data")
    logger.info("request_data = {}".format(request_data))
    try:
        username = request_data["name"]
        get_user_response = cognito_client.admin_get_user(
            UserPoolId=USER_POOL_ID,
            Username=username
        )
        user_data = UserDetailsDAO.get_data(username, session)
        if user_data:
            data_dict = user_data.to_dict()
            data_dict.update({
                "user_permission": [json.loads(d['Value']) for d in
                                    get_user_response[
                                        'UserAttributes'] if
                                    d['Name'].startswith('custom')][0]
            })
            message = "User Data Found"
            response_payload = AppServices.app_response(200, message, True,
                                                        data_dict)
            return response_payload

        else:
            message = "User Data Not Found"
            response_payload = AppServices.app_response(404, message, True,
                                                        {})
            return response_payload

    except Exception as e:
        logger.error("get_user_data error = {}".format(e))
        message = "Something went wrong!!"
        response_payload = AppServices.app_response(500, message, False, {})
        return response_payload


# context = "function:dev"
# event = {
#     "name": "user1@gmail.com",
#     "username": "a35c9ea9-409c-4c29-9f36-9cca05fe469a"
# }
# response_payload = lambda_handler(event, context)
# print(response_payload)