import base64
import datetime
import hashlib
import hmac
import json
import logging
import random
import re
import string
from configparser import ConfigParser

import boto3

from config import db_connection
from dao import RegistrationOtpHistoryDAO, UserDetailsDAO, TenantDetailsDAO
from models import Base, UserDetailsVO, RegistrationOtpHistoryVO
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
    attributes = ["user_request_id", "username", "first_name", "last_name",
                  "dob"]
    request_data_keys = request_data.keys()
    for attribute in attributes:
        if attribute in request_data_keys and request_data[attribute]:
            pass
        else:
            return False, attribute
    return True, ""


def get_secret_hash(username):
    msg = username + CLIENT_ID
    encoded_digest = hmac.new(str(CLIENT_SECRET).encode('utf-8'),
                              msg=str(msg).encode('utf-8'),
                              digestmod=hashlib.sha256).digest()
    decoded_digest = base64.b64encode(encoded_digest).decode()
    return decoded_digest


def password_generate():
    pwd_length = 12
    pwlist = ([random.choice(string.punctuation),
               random.choice(string.digits),
               random.choice(string.ascii_lowercase),
               random.choice(string.ascii_uppercase),
               ]
              + [random.choice(string.ascii_lowercase
                               + string.ascii_uppercase
                               + string.punctuation
                               + string.digits) for i in range(pwd_length)])
    random.shuffle(pwlist)
    pw = ''.join(pwlist)
    return pw


def register_verify_user(request_data, request_tenant_name, session):
    username = request_data['username']
    user_request_id = request_data["user_request_id"]
    permission = request_data['permission']
    user_otp_data = RegistrationOtpHistoryDAO.get_user_details(session,
                                                               username,
                                                               user_request_id)
    if not user_otp_data:
        message = "Invalid User request data, user otp data not found."
        response_payload = AppServices.app_response(400, message,
                                                    False, {})
        return response_payload

    group_name = user_otp_data.tenant_name

    if not group_name == request_tenant_name:
        message = "Tenant Details invalid."
        response_payload = AppServices.app_response(400, message,
                                                    False, {})
        return response_payload

    if user_otp_data.user_status == "unconfirmed":
        message = "user is unconfirmed, please complete register process."
        response_payload = AppServices.app_response(400, message,
                                                    False, {})
        return response_payload

    password = password_generate()
    secret_hash = get_secret_hash(username)

    try:
        is_user_created = create_user_add_in_group(username, password,
                                                   group_name, permission)
        if not is_user_created:
            message = "Got error in user create and add into group."
            response_payload = AppServices.app_response(500, message,
                                                        False, {})
            return response_payload

        login_resp = cognito_client.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow="CUSTOM_AUTH",
            AuthParameters={
                "USERNAME": username,
                "SECRET_HASH": secret_hash
            },
        )

        if login_resp['ChallengeName'] == 'CUSTOM_CHALLENGE':
            resp = cognito_client.admin_set_user_password(
                UserPoolId=USER_POOL_ID,
                Username=username,
                Password=password,
                Permanent=True
            )

            if resp['ResponseMetadata']['HTTPStatusCode'] == 200:
                is_inserted = insert_user_details(request_data,
                                                  user_otp_data, session)
                logger.info(
                    "user details insert status = {}".format(is_inserted))
                message = "User Registration successful."
                response_payload = AppServices.app_response(200, message, True,
                                                            {})
                return response_payload
            else:
                message = "Registration failed!!"
                response_payload = AppServices.app_response(500,
                                                            message,
                                                            False, {})
                return response_payload

        else:
            message = "Registration failed due to challenge"
            response_payload = AppServices.app_response(500, message,
                                                        False, {})
            return response_payload

    except cognito_client.exceptions.UsernameExistsException:
        logger.info("user already exist")
        message = "User already exist!!"
        response_payload = AppServices.app_response(400, message, False, {})
        return response_payload

    except Exception as registration_error:
        logger.error(ERROR_FORMAT.format(registration_error.__str__(),
                                         "register_user"))
        message = "Some thing went wrong!!"
        response_payload = AppServices.app_response(500, message, False, {})
        return response_payload


def create_user_add_in_group(username, password, group_name, permission):
    try:
        if re.search('@', username):
            user_attributes = [
                {
                    'Name': "name",
                    'Value': username
                },
                {
                    'Name': "email",
                    'Value': username
                },
                {
                    'Name': 'email_verified',
                    'Value': 'true',
                },
                {
                    'Name': 'custom:permission',
                    'Value': json.dumps(permission)
                },

            ]

        else:
            user_attributes = [
                {
                    'Name': "phone_number",
                    'Value': username
                },
                {
                    'Name': 'phone_number_verified',
                    'Value': 'true',
                },
                {
                    'Name': 'custom:permission',
                    'Value': json.dumps(permission)
                },

            ]

        # response = cognito_client.add_custom_attributes(
        #     UserPoolId=USER_POOL_ID,
        #     CustomAttributes=[
        #         {
        #             'Name': 'permission',
        #             'AttributeDataType': 'String'
        #         }
        #         ]
        #     )

        create_user_resp = cognito_client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=username,
            UserAttributes=user_attributes,
            ValidationData=[
                {
                    'Name': "custom:username",
                    'Value': username
                }
            ],
            TemporaryPassword=password,
            MessageAction='SUPPRESS'
        )

        cognito_client.admin_add_user_to_group(
            UserPoolId=USER_POOL_ID,
            Username=username,
            GroupName=group_name
        )

        cognito_client.admin_add_user_to_group(
            UserPoolId=USER_POOL_ID,
            Username=username,
            GroupName='USER'
        )
        return create_user_resp

    except cognito_client.exceptions.ResourceNotFoundException:
        logger.info("group not found")
        return ""


def insert_user_details(request_data, user_otp_data, session):
    try:
        username = request_data['username']
        first_name = request_data['first_name']
        last_name = request_data['last_name']
        dob = request_data['dob']
        tenant_data = RegistrationOtpHistoryDAO.get_tenant(session,
                                                           user_otp_data.tenant_name)
        user_details_vo = UserDetailsVO()
        user_details_vo.username = username
        user_details_vo.first_name = first_name
        user_details_vo.last_name = last_name
        user_details_vo.dob = dob
        user_details_vo.created_at = datetime.datetime.utcnow().isoformat()
        user_details_vo.updated_at = datetime.datetime.utcnow().isoformat()
        user_details_vo.tenant_id = tenant_data.id
        UserDetailsDAO.insert_user_details(user_details_vo, session)

        registration_otp_vo = RegistrationOtpHistoryVO()
        registration_otp_vo.user_status = "confirmed"
        user_id = user_otp_data.id
        registration_otp_vo.id = user_id
        RegistrationOtpHistoryDAO.update_user_status(registration_otp_vo,
                                                     session)
        return {"username": user_details_vo.username,
                "first_name": user_details_vo.first_name,
                "last_name": user_details_vo.last_name,
                "dob": user_details_vo.dob.isoformat()}

    except Exception as e:
        logger.error("Got error in insert_user_details = {}".format(e))
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

    response_payload = register_verify_user(request_data,
                                            request_tenant_name, session)
    logger.info("final response_payload = {}".format(response_payload))
    return response_payload

# context = "function:dev"
# event = {
#     'username': 'user1@gmail.com',
#     'user_request_id': '9b171e0c-bccc-11ed-af27-9bef1486d2d9',
#     'first_name': 'user1',
#     'last_name': 'user1',
#     'dob': '2000-8-9',
#     'permission': [
#         "APP_DASHBOARD",
#         "APP_HOME"
#     ]
# "permission":[
#     {
#     "type":"SCREEN", "permission":"READ WRITE"
#     },
#     {
#         "type":"DATA","permission":"UPDATE"
#     }
# ]

# }

# response_payload = lambda_handler(event, context)
# print(response_payload)
