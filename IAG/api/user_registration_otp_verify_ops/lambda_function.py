import base64
import datetime
import logging
from configparser import ConfigParser

import boto3

from config import db_connection
from dao import RegistrationOtpHistoryDAO, TenantDetailsDAO, UserOtpHistoryDAO
from models import Base, RegistrationOtpHistoryVO
from services import AppServices

logger = logging.getLogger("ksi_user_registration_operations")
logger.setLevel(logging.INFO)

configure = ConfigParser()
configure.read('config.ini')

cognito_client = boto3.client('cognito-idp')

ERROR_FORMAT = configure.get('ERROR_HANDLING', 'format')

USER_POOL_ID = configure.get('COGNITO_CONFIG', 'user_pool_id')
CLIENT_ID = configure.get('COGNITO_CONFIG', 'client_id')
CLIENT_SECRET = configure.get('COGNITO_CONFIG', 'client_secret')


def validate_request(request_data):
    logger.info("Function validate_request")
    logger.info("params: request_data = {}".format(request_data))
    attributes = ["user_request_id", "username", "otp"]
    request_data_keys = request_data.keys()
    for attribute in attributes:
        if attribute in request_data_keys and request_data[attribute]:
            pass
        else:
            return False, attribute
    return True, ""


def user_verify_otp(request_data, request_tenant_name, session):
    logger.info("Function: user_verify_otp")
    logger.info("Params: request_data = {}".format(request_data))
    username = request_data['username']
    otp = request_data['otp']
    user_request_id = request_data["user_request_id"]
    user_otp_data = RegistrationOtpHistoryDAO.get_user_details(session,
                                                               username,
                                                               user_request_id)
    if not user_otp_data:
        message = "You are not registered, yet please verify your account " \
                  "first."
        response_payload = AppServices.app_response(404, message, False, {})
        return response_payload

    group_name = user_otp_data.tenant_name
    if not group_name == request_tenant_name:
        message = "Tenant Details invalid."
        response_payload = AppServices.app_response(400, message,
                                                    False, {})
        return response_payload

    if user_otp_data.user_status == "confirm":
        message = "You are already registered, Please login!!"
        response_payload = AppServices.app_response(400, message,
                                                    False, {})
        return response_payload

    if otp != user_otp_data.otp:
        message = "invalid otp"
        response_payload = AppServices.app_response(403, message, False, {})
        return response_payload

    if user_otp_data.otp_expire_time < datetime.datetime.utcnow().strftime(
            "%Y-%m-%d %H:%M:%S"):
        message = "Your otp has been expired!!"
        response_payload = AppServices.app_response(403, message, False, {})
        return response_payload

    user_status = "confirm"
    user_id = user_otp_data.id
    is_update = update_user_status(user_status, user_id, session)
    logger.info("user update status = {}".format(is_update))
    message = "Otp Verified"
    response_payload = AppServices.app_response(200, message, True,
                                                {})

    return response_payload


def update_user_status(user_status, user_id, session):
    try:
        user_otp_history_vo = RegistrationOtpHistoryVO()
        user_otp_history_vo.id = user_id
        user_otp_history_vo.user_status = user_status
        UserOtpHistoryDAO.update_otp_history(user_otp_history_vo, session)
        return True
    except Exception as e:
        logger.error("Error in update_user_status ={}".format(e))
        return False


def lambda_handler(event, context):
    logger.info("Params: event = {}".format(event))

    server_alias = AppServices.get_env(context)
    logger.info("got env = {}".format(server_alias))

    db_engine, session = db_connection(server_alias)
    Base.metadata.create_all(db_engine)

    request_data = event["body"]
    is_valid, attribute = validate_request(request_data)

    if not is_valid:
        message = "{} required, not found".format(attribute)
        response_payload = AppServices.app_response(400, message, False, {})
        return response_payload

    basic_auth = event.get('headers', {}).get('Authorization', '').split(' ')
    if not basic_auth or basic_auth[0] != "Basic":
        return {
            'statusCode': 401,
            'headers': {'WWW-Authenticate': 'Basic'},
            'body': 'Unauthorized'
        }
    auth_tenant_details = base64.b64decode(basic_auth[-1].encode(
        "utf-8")).decode("utf-8").split(":")
    tenant_secret_id = auth_tenant_details[0]
    tenant_secret_key = auth_tenant_details[1]
    logger.info(
        "tenant_secret_id = {}, tenant_secret_key = {}".format(
            tenant_secret_id, tenant_secret_key))

    tenant_details = TenantDetailsDAO.get_data(tenant_secret_id,
                                               tenant_secret_key, session)
    if not tenant_details:
        message = "Invalid tenant details."
        response_payload = AppServices.app_response(400, message, False, {})
        return response_payload

    request_tenant_name = tenant_details.tenant_name

    response_payload = user_verify_otp(request_data, request_tenant_name,
                                       session)
    logger.info("final response_payload = {}".format(response_payload))
    return response_payload

# context = "function:dev"
# event = {"body":{
#     'username': 'user4@gmail.com',
#     'user_request_id': 'b46d3162-be5b-11ed-a5d5-95e1d2e1277e',
#     'otp': '092332'
# }}
#
# response_payload = lambda_handler(event, context)
# print(response_payload)
