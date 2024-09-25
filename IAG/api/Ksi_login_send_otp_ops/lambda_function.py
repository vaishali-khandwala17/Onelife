import base64
import hashlib
import hmac
import logging
import boto3
from configparser import ConfigParser
import random
import string
from botocore.exceptions import ClientError
from services import AppServices

logger = logging.getLogger("ksi_login_operations")
logger.setLevel(logging.INFO)

configure = ConfigParser()
configure.read('config.ini')

cognito_client = boto3.client('cognito-idp')
sns_client = boto3.client('sns')

ERROR_FORMAT = configure.get('ERROR_HANDLING', 'format')

USER_POOL_ID = configure.get('COGNITO_CONFIG', 'user_pool_id')
CLIENT_ID = configure.get('COGNITO_CONFIG', 'client_id')
CLIENT_SECRET = configure.get('COGNITO_CONFIG', 'client_secret')


def password_generate():
    pwd_length = 12
    pw_list = ([random.choice(string.punctuation),
                random.choice(string.digits),
                random.choice(string.ascii_lowercase),
                random.choice(string.ascii_uppercase),
                ] + [random.choice(string.ascii_lowercase
                                   + string.ascii_uppercase + string.punctuation + string.digits)
                     for i in range(pwd_length)])
    random.shuffle(pw_list)
    final_password = ''.join(pw_list)
    return final_password


def get_secret_hash(username):
    msg = username + CLIENT_ID
    encoded_digest = hmac.new(str(CLIENT_SECRET).encode('utf-8'),
                              msg=str(msg).encode('utf-8'),
                              digestmod=hashlib.sha256).digest()
    decoded_digest = base64.b64encode(encoded_digest).decode()
    return decoded_digest


def ksi_login(request_data):
    logger.info("Function: ksi_login_ops")
    logger.info("Params: request_data = {}".format(request_data))
    try:
        secret_hash = get_secret_hash(request_data["username"])
        response = cognito_client.initiate_auth(
            AuthFlow='CUSTOM_AUTH',
            ClientId=CLIENT_ID,
            AuthParameters={
                'USERNAME': request_data["username"],
                "SECRET_HASH": secret_hash
            }
        )
        if "ChallengeParameters" in response:
            otp = response["ChallengeParameters"]["answer"]
            session = response["Session"]
            otp_message = f'Your OTP is {otp}'

            data = {
                'otp': otp,
                'session': session,
                'username': request_data["username"]
            }
            message = "user verification Code send successfully."
            response_payload = AppServices.app_response(200, message, True,
                                                        data)
            return response_payload

        message = "User login error."
        response_payload = AppServices.app_response(500, message, False,
                                                    {})
        return response_payload

    except ClientError as e:
        if e.response['Error']['Code'] == 'NotAuthorizedException':
            message = "User is not registered, Please register."
            response_payload = AppServices.app_response(404, message, False,
                                                        {})
            return response_payload
        else:
            message = "Something went wrong - Client error"
            response_payload = AppServices.app_response(500, message, False,
                                                        {})
            return response_payload

    except Exception as e:
        logger.error("login_ksi error = {}".format(e))
        message = "Something went wrong!!"
        response_payload = AppServices.app_response(500, message, False, {})
        return response_payload


def lambda_handler(event, context):
    logger.info("Params: event = {}".format(event))

    server_alias = AppServices.get_env(context)
    logger.info("got env = {}".format(server_alias))

    if "username" not in event:
        message = "username required, not found."
        response_payload = AppServices.app_response(400, message, False, {})
        return response_payload

    response_payload = ksi_login(event)
    logger.info("final response_payload = {}".format(response_payload))
    return response_payload


# context = "function:dev"
# event_body = {
#     'username': 'admin@yopmail.com'
# }
#
# response_payload = lambda_handler(event_body, context)
# print(response_payload)
