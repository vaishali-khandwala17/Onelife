import base64
import hashlib
import hmac
import json
import logging
from configparser import ConfigParser

import boto3
from botocore.exceptions import ClientError

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


def validate_request(request_data):
    logger.info("Function validate_request")
    logger.info("params: request_data = {}".format(request_data))
    attributes = ["otp", "session", "username"]
    request_data_keys = request_data.keys()
    for attribute in attributes:
        if attribute in request_data_keys and request_data[attribute]:
            pass
        else:
            return False, attribute
    return True, ""


def lambda_handler(event, context):
    logger.info("Params: event = {}".format(event))

    server_alias = AppServices.get_env(context)
    logger.info("got env = {}".format(server_alias))

    is_valid, attribute = validate_request(event)

    if not is_valid:
        message = "{} required, not found.".format(attribute)
        response_payload = AppServices.app_response(400, message, False, {})
        return response_payload

    response_payload = ksi_login_verify(event)
    logger.info("final response_payload = {}".format(response_payload))
    return response_payload


def get_secret_hash(username):
    msg = username + CLIENT_ID
    encoded_digest = hmac.new(str(CLIENT_SECRET).encode('utf-8'),
                              msg=str(msg).encode('utf-8'),
                              digestmod=hashlib.sha256).digest()
    decoded_digest = base64.b64encode(encoded_digest).decode()
    return decoded_digest


def ksi_login_verify(request_data):
    logger.info("Function: ksi_login_ops")
    logger.info("Params: request_data = {}".format(request_data))
    try:
        username = request_data["username"]
        otp = request_data["otp"]
        session = request_data["session"]
        secret_hash = get_secret_hash(request_data["username"])
        respond_to_auth_response = cognito_client.respond_to_auth_challenge(
            ClientId=CLIENT_ID,
            Session=session,
            ChallengeName='CUSTOM_CHALLENGE',
            ChallengeResponses={
                'USERNAME': username,
                'ANSWER': otp,
                "SECRET_HASH": secret_hash
            }
        )

        get_user_response = cognito_client.admin_get_user(
            UserPoolId=USER_POOL_ID,
            Username=username
        )
        custom_attr = [d for d in get_user_response['UserAttributes'] if
                       d['Name'].startswith('custom')]
        if custom_attr:
            user_permission = json.loads(custom_attr[0]['Value'])
        else:
            user_permission = None
        data = {
            "access_token": respond_to_auth_response["AuthenticationResult"][
                "AccessToken"],
            "id_token": respond_to_auth_response["AuthenticationResult"][
                "IdToken"],
            "refresh_token": respond_to_auth_response["AuthenticationResult"][
                "RefreshToken"],
            "user_info": {
                "user_permission": user_permission,
                "username": username
            }
        }
        message = "Login Success!!"
        response_payload = AppServices.app_response(200, message, True,
                                                    data)
        return response_payload

    except ClientError as e:

        if e.response['Error']['Code'] == 'CodeMismatchException':
            message = "Please enter valid otp for complete login process."
            response_payload = AppServices.app_response(404, message, False,
                                                        {})
            return response_payload
        elif e.response['Error']['Code'] == 'NotAuthorizedException':
            message = "Unauthorized!!"
            response_payload = AppServices.app_response(403, message, False,
                                                        {})
            return response_payload

    except Exception as e:
        logger.error("login_ksi error = {}".format(e))
        message = "Something went wrong!!"
        response_payload = AppServices.app_response(500, message, False, {})
        return response_payload


# context = "function:dev"
# event_body = {
#     "otp": "493493",
#     "session": "AYABeJvUfWfFVKGjxnBILy4glgIAHQABAAdTZXJ2aWNlABBDb2duaXRvVXNlclBvb2xzAAEAB2F3cy1rbXMAS2Fybjphd3M6a21zOnVzLWVhc3QtMjo0MTc1Njc5MDM0Njk6a2V5LzVjZDI0ZDRjLWVjNWItNGU4Ny05MGI2LTVkODdkOTZmY2RkMgC4AQIBAHjif3k0w30uAyP92ifoZ0jN6g50UW_KR0w9Vv2c_wlQAgGUDibf6eSDuAL5iUwy999LAAAAfjB8BgkqhkiG9w0BBwagbzBtAgEAMGgGCSqGSIb3DQEHATAeBglghkgBZQMEAS4wEQQM85llqH3gVtcN5MctAgEQgDv_fQP9LIBfxp8HRa36JRxyltj4X-eHze1YGoNuvFWeEH8cnrMsA-JM1FyO0DjkwMnjjOUJzFw-WZwUqAIAAAAADAAAEAAAAAAAAAAAAAAAAADdPbC8qsowIaw2kKhXMz8I_____wAAAAEAAAAAAAAAAAAAAAEAAAESkK6tr86f9XEULS6iE0_fc90gP821HbRg3xmjjuCksJPe-9rxmycyRNPuh84owR7-OoUn9xIx-J2EiunLqS2R1-7Yd9sVilJ5RT-sOrLrkqtM_qRW6B3UX7zR98OWkMHxfE4EGdwWgDZ5G2P3H_nPBK2lMfajwBv-cwmBRmz1G-ri53V850d-sqeeJrZZFuKP57E3pG0HW-FM3P-ZuciVBoBiv1wrXy3tvClyxMf2uLukAV-k84SVWf-oljyVGBl5dqkX4XQS5mB5CP982QUFKGjJcOrfbHB-y99r2hsTnp67sn-SBP6YYsMh_nDmcVfvJq8v_LtYQLoeWxVi6K_eT_aXfCArlQmgXdI8rPPON6Ty32D1DkPsknEBwVUbcADZRvU",
#     "username": "admin@yopmail.com"
# }
# response_payload = lambda_handler(event_body, context)
# print(response_payload)
