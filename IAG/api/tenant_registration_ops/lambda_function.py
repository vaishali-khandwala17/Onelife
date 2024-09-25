import base64
import datetime
import hashlib
import hmac
import logging
import random
import re
import string
import uuid
from configparser import ConfigParser

import boto3
from botocore.exceptions import ClientError

from config import db_connection
from dao import TenantDetailsDAO
from models import Base, TenantDetailsVO
from services import AppServices

logger = logging.getLogger("ksi_tenant_registration_operations")
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
    attributes = ["tenant_name", "username"]
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


def create_group(group_name):
    try:
        cognito_client.create_group(UserPoolId=USER_POOL_ID,
                                    GroupName=group_name)
        logger.info("new group created")
        return True, ""
    except cognito_client.exceptions.GroupExistsException:
        logger.info("group already exists")
        return True, ""
    except Exception as e:
        logger.error("Got Exception in create_group = {}".format(e))
        message = "Something wen wrong!!"
        response_payload = AppServices.app_response(500, message, False, {})
        return False, response_payload


def username_valid(username):
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    phone_pattern = r'^\+[1-9]\d{1,14}$'
    if re.match(email_pattern, username):
        return True, "email"
    elif re.match(phone_pattern, username):
        return True, "phone"
    else:
        return False, ""


def create_user_add_in_group(username, username_type, password, tenant_name):
    logger.info("Function: create_user_add_in_group")
    logger.info("Params: username = {}, password = {}, tenant_name ={}, "
                "username_type = {}".format(username, password, tenant_name,
                                            username_type))
    try:
        if username_type == "email":
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
                }
            ]
        else:
            user_attributes = [
                {
                    'Name': "name",
                    'Value': username
                },
                {
                    'Name': "phone_number",
                    'Value': username
                },
                {
                    'Name': 'phone_number_verified',
                    'Value': 'true',
                }
            ]
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
            GroupName=tenant_name
        )
        cognito_client.admin_add_user_to_group(
            UserPoolId=USER_POOL_ID,
            Username=username,
            GroupName="TENANT"
        )
        cognito_client.admin_add_user_to_group(
            UserPoolId=USER_POOL_ID,
            Username=username,
            GroupName="USER"
        )
        return True, create_user_resp

    except ClientError as e:
        if e.response['Error']['Code'] == 'UsernameExistsException':
            message = "user already exist!!."
            response_payload = AppServices.app_response(400, message, False,
                                                        {})
            return False, response_payload
        else:
            message = "Client error - {}.".format(e)
            response_payload = AppServices.app_response(400, message, False,
                                                        {})
            return False, response_payload

    except Exception as e:
        logger.error(
            "got exception in create_user_add_in_group = {}".format(e))
        message = "Got error in user create and add into group."
        response_payload = AppServices.app_response(500, message, False,
                                                    {})
        return False, response_payload


def insert_tenant_details(request_data, session):
    try:
        tenant_details_vo = TenantDetailsVO()
        tenant_details_vo.tenant_name = request_data["tenant_name"]
        tenant_details_vo.username = request_data["username"]
        tenant_details_vo.tenant_secret_id = request_data["tenant_secret_id"]
        tenant_details_vo.tenant_secret_key = request_data["tenant_secret_key"]
        tenant_details_vo.created_at = datetime.datetime.utcnow().isoformat()
        tenant_details_vo.updated_at = datetime.datetime.utcnow().isoformat()
        TenantDetailsDAO.insert_tenant_details(tenant_details_vo, session)
        return True
    except Exception as e:
        logger.error("Got exception in insert_tenant_details = {}".format(e))
        return False


def register_tenant(request_data, session):
    logger.info("Function: register_tenant")
    logger.info("Params: request_data = {}".format(request_data))
    try:
        username_type = request_data["username_type"]
        username = request_data["username"]
        tenant_name = request_data["tenant_name"].replace(" ", "_").upper()
        secret_id = str(uuid.uuid1())
        secret_key = str(uuid.uuid4())
        secret_hash = get_secret_hash(username)
        password = password_generate()
        logger.info("username = {}, tenant_name = {}, secret_id = {}, "
                    "secret_key  = {}, secret_hash = {}, password = {}"
                    .format(username, tenant_name, secret_id, secret_key,
                            secret_hash, password))

        is_group_created, response_payload = create_group(tenant_name)
        if not is_group_created:
            return response_payload

        is_created, response_payload = create_user_add_in_group(username,
                                                                username_type,
                                                                password,
                                                                tenant_name)
        if not is_created:
            return response_payload

        login_resp = cognito_client.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow="CUSTOM_AUTH",
            AuthParameters={
                "USERNAME": username,
                "SECRET_HASH": secret_hash
            }
        )
        if login_resp['ChallengeName'] == 'CUSTOM_CHALLENGE':
            resp = cognito_client.admin_set_user_password(
                UserPoolId=USER_POOL_ID,
                Username=username,
                Password=password,
                Permanent=True
            )
            if resp['ResponseMetadata']['HTTPStatusCode'] == 200:
                tenant_data = {
                    'tenant_name': tenant_name,
                    'username': username,
                    'tenant_secret_id': secret_id,
                    "tenant_secret_key": secret_key
                }
                is_inserted = insert_tenant_details(tenant_data, session)
                logger.info(
                    "tenant details insert status = {}".format(is_inserted))
                if not is_inserted:
                    message = "Registration failed!!"
                    response_payload = AppServices.app_response(500, message,
                                                                False, {})
                    return response_payload

                message = "Tenant Registration successful."
                response_payload = AppServices.app_response(200, message, True,
                                                            tenant_data)
                return response_payload
            else:
                message = "Registration failed!!"
                response_payload = AppServices.app_response(500, message,
                                                            False, {})
                return response_payload
        else:
            message = "Registration failed due to challenge!!"
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
                                         "register_tenant"))
        message = "Something wen wrong!!"
        response_payload = AppServices.app_response(500, message, False, {})
        return response_payload


def lambda_handler(event, context):
    logger.info("Params: event = {}".format(event))

    server_alias = AppServices.get_env(context)
    logger.info("got env = {}".format(server_alias))

    db_engine, session = db_connection(server_alias)
    Base.metadata.create_all(db_engine)

    admin_username = event["headers"]["name"]
    admin_group_response = cognito_client.admin_list_groups_for_user(
        UserPoolId=USER_POOL_ID,
        Username=admin_username
    )
    logger.info("admin_group_response = {}".format(admin_group_response))
    user_groups = [group['GroupName'] for group in
                   admin_group_response['Groups']]
    if "ADMIN" not in user_groups:
        message = "Unauthorized, only admin can create Tenant."
        response_payload = AppServices.app_response(403, message, False, {})
        return response_payload

    request_data = event["body"]
    is_valid, attribute = validate_request(request_data)
    if not is_valid:
        message = "{} required, not found".format(attribute)
        response_payload = AppServices.app_response(400, message, False, {})
        return response_payload

    tenant_name = request_data["tenant_name"].replace(" ", "_").upper()

    if tenant_name in ["ADMIN", "TENANT", "USER"]:
        message = "Tenant Name is not valid."
        response_payload = AppServices.app_response(400, message, False, {})
        return response_payload

    is_valid, username_type = username_valid(request_data["username"])
    if not is_valid:
        message = "username format is not valid."
        response_payload = AppServices.app_response(400, message, False, {})
        return response_payload

    tenant_data = TenantDetailsDAO.get_data(tenant_name, session)

    if tenant_data:
        message = "Tenant is already registered!!"
        response_payload = AppServices.app_response(400, message, False, {})
        return response_payload

    request_data["username_type"] = username_type
    response_payload = register_tenant(request_data, session)
    logger.info("Final response_payload = {}".format(response_payload))
    return response_payload

# context = "function:dev"
# event_body = {
#     'tenant_name': 'tenant9',
#     'username': '+919737986964',
# }
# response_payload = lambda_handler(event_body, context)
# print(response_payload)
