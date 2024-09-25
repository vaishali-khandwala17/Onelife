import base64
import datetime
import hashlib
import hmac
import logging
import math
import random
import re
import uuid
from configparser import ConfigParser

import boto3

from config import db_connection
from dao import RegistrationOtpHistoryDAO, TenantDetailsDAO
from models import Base, RegistrationOtpHistoryVO
from services import AppServices

logger = logging.getLogger("ksi_registration_otp_history_operations")
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
    attributes = ["username"]
    request_data_keys = request_data.keys()
    for attribute in attributes:
        if attribute in request_data_keys and request_data[attribute]:
            pass
        else:
            return False, attribute
    return True, ""


def generate_otp():
    """
    This is used to generate random otp for the user to send in the public challenge params
    :return: string
    """
    # Declare a string variable which stores all string
    string = '0123456789'
    OTP = ""
    length = len(string)
    for index in range(6):
        OTP += string[math.floor(random.random() * length)]
    return OTP


def username_valid(username):
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    phone_pattern = r'^\+[1-9]\d{1,14}$'
    if re.match(email_pattern, username):
        return True, "email"
    elif re.match(phone_pattern, username):
        return True, "phone"
    else:
        return False, ""


def get_secret_hash(username):
    msg = username + CLIENT_ID
    encoded_digest = hmac.new(str(CLIENT_SECRET).encode('utf-8'),
                              msg=str(msg).encode('utf-8'),
                              digestmod=hashlib.sha256).digest()
    decoded_digest = base64.b64encode(encoded_digest).decode()
    return decoded_digest


def register_user(request_data, session):
    logger.info("Function: register_user")
    logger.info("Params: request_data = {}".format(request_data))
    try:
        username = request_data["username"]
        tenant_name = request_data["tenant_name"].replace(" ", "_").upper()
        otp = generate_otp()
        current_time = datetime.datetime.utcnow().isoformat()
        otp_expire = str(datetime.datetime.utcnow() + \
                         datetime.timedelta(hours=1))
        user_request_id = str(uuid.uuid1())

        user_otp_status_data = RegistrationOtpHistoryDAO.get_data(username,
                                                                  session)
        registration_otp_vo = RegistrationOtpHistoryVO()
        is_update = False
        if user_otp_status_data:
            if user_otp_status_data.user_status == "confirm":
                message = "You are already registered, Please login!!"
                response_payload = AppServices.app_response(400, message,
                                                            False, {})
                return response_payload
            else:
                is_update = True
                registration_otp_vo.id = user_otp_status_data.id

        registration_otp_vo.user_request_id = user_request_id
        registration_otp_vo.otp = otp
        registration_otp_vo.otp_expire_time = otp_expire
        registration_otp_vo.user_status = "unconfirmed"
        tenant_data = TenantDetailsDAO.get_tenant(session,tenant_name)
        registration_otp_vo.tenant_id = tenant_data.id
        registration_otp_vo.tenant_name = tenant_name
        registration_otp_vo.username = username
        registration_otp_vo.created_at = current_time
        registration_otp_vo.updated_at = current_time
        if is_update:
            RegistrationOtpHistoryDAO.update(registration_otp_vo, session)
        else:
            RegistrationOtpHistoryDAO.insert_registration_otp_history(
                registration_otp_vo, session)

        user_data = {
            'otp': otp,
            'user_request_id': user_request_id,
            'otp_expire_time': otp_expire
        }
        logger.info("user_data = {}".format(user_data))

        message = "User registration Process initiated."
        response_payload = AppServices.app_response(200, message, False,
                                                    user_data)
        return response_payload

    except Exception as e:
        logger.error(ERROR_FORMAT.format(e.__str__(), "register_user"))
        message = "Something went wrong!!"
        response_payload = AppServices.app_response(500, message, False, {})
        return response_payload


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

    tenant_name = tenant_details.tenant_name
    request_data["tenant_name"] = tenant_name

    is_valid, username_type = username_valid(request_data["username"])
    if not is_valid:
        message = "username format is not valid."
        response_payload = AppServices.app_response(400, message, False, {})
        return response_payload

    request_data["username_type"] = username_type
    response_payload = register_user(request_data, session)
    logger.info("final response_payload = {}".format(response_payload))
    return response_payload

# context = "function:dev"
# event = {'headers': {'Authorization': 'Basic '
#                                       'NWFkYjlkYzAtYmU0Ni0xMWVkLWE5YTctMDlmNzFlYzQyODk0OjI1ZjJjNDRkLTJhNGUtNDM2NS1hMGU0LTM0YzVhYzFhZTAwZg=='}, 'body': {'username': 'user4@gmail.com'}}
#
# response_payload = lambda_handler(event, context)
# print(response_payload)
