import json
import logging
from configparser import ConfigParser

import boto3

from config import db_connection
from dao import UserDetailsDAO,TenantDetailsDAO,RegistrationOtpHistoryDAO
from models import Base
from services import AppServices

logger = logging.getLogger("ksi_user_listing_operations")
logger.setLevel(logging.INFO)

cognito_client = boto3.client('cognito-idp')

configure = ConfigParser()
configure.read('config.ini')

USER_POOL_ID = configure.get('COGNITO_CONFIG', 'user_pool_id')
ERROR_FORMAT = configure.get('ERROR_HANDLING', 'format')


def validate_request(request_data):
    logger.info("Function validate_request")
    logger.info("params: request_data = {}".format(request_data))
    attributes = ["page_number", "page_size", "username"]
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

    db_engine, session = db_connection(server_alias)
    Base.metadata.create_all(db_engine)

    request_data = event["body"]
    username = event["headers"]["name"]
    request_data["username"] = username
    is_valid, attribute = validate_request(request_data)

    if not is_valid:
        message = "{} parameter missing or invalid.".format(attribute)
        response_payload = AppServices.app_response(400, message, False, {})
        return response_payload

    response_payload = get_user_details(request_data, session)
    logger.info("final response_payload = {}".format(response_payload))
    return response_payload


def get_user_details(request_data, session):
    logger.info("function:get_user_details")
    logger.info("Params: request_data = {}".format(request_data))
    try:
        username = request_data["username"]
        admin_group_response = cognito_client.admin_list_groups_for_user(
            UserPoolId=USER_POOL_ID,
            Username=username
        )
        logger.info("admin_group_response = {}".format(admin_group_response))
        user_groups = [group['GroupName'] for group in
                       admin_group_response['Groups']]

        page_number = int(request_data["page_number"])
        limit = int(request_data["page_size"])
        skip = (page_number - 1) * limit
        search_value = request_data.get("search_value", None)

        if "ADMIN" in user_groups:
            user_details_list = []
            user_list = RegistrationOtpHistoryDAO.get_user_data(session,
                                                                skip,limit,search_value)
            for user in user_list:
                if user.user_status == "confirmed":
                    user_status = user.user_status
                    username = user.username
                    user_data_list = UserDetailsDAO.get_data(session,skip,
                                                            limit,username)

                    for user in user_data_list:
                        user_data_dict = user.to_dict()
                        username = user_data_dict['username']
                        user_data = UserDetailsDAO.get_tenant_id(session,
                                                                 username)
                        tenant_id = user_data.tenant_id
                        tenant_data = TenantDetailsDAO.get_tenant_name(session,tenant_id)
                        tenant_name = tenant_data.tenant_name
                        get_user_response = cognito_client.admin_get_user(
                            UserPoolId=USER_POOL_ID,
                            Username=username
                        )
                        user_data_dict.update({
                            "user_status":user_status,
                            "tenant_name": tenant_name,
                            "user_permission": [json.loads(d['Value']) for d in
                                                get_user_response[
                                                    'UserAttributes'] if
                                                d['Name'].startswith(
                                                    'custom')][0]
                        })

                        user_details_list.append(user_data_dict)

                    if not user_data_list:
                        message = "Data not found!!"
                        response_payload = AppServices.app_response(404, message, False,
                                                                    [])
                        return response_payload
                else:
                    user_data_dict = {}
                    data = {
                        "username":user.username,
                        "user_status":user.user_status,
                        "first_name":"",
                        "last_name":"",
                        "dob":"",
                        "user_permission":""
                    }
                    user_data_dict.update(data)
                    user_details_list.append(user_data_dict)

        elif "TENANT" in user_groups:
            tenant_data = TenantDetailsDAO.get_tenant_data(session, username)
            tenant_id = tenant_data.id
            user_data_list = UserDetailsDAO.get_tenant_user_data(session,
                                                                 tenant_id,
                                                                 skip, limit)
            user_details_list = []

            for user in user_data_list:
                user_data_dict = user.to_dict()
                username = user_data_dict['username']
                user_data = UserDetailsDAO.get_tenant_id(session, username)
                tenant_id = user_data.tenant_id
                tenant_data = TenantDetailsDAO.get_tenant_name(session, tenant_id)
                tenant_name = tenant_data.tenant_name
                get_user_response = cognito_client.admin_get_user(
                    UserPoolId=USER_POOL_ID,
                    Username=username
                )
                user_data_dict.update({
                    "tenant_name": tenant_name,
                    "user_permission": [json.loads(d['Value']) for d in
                                        get_user_response[
                                            'UserAttributes'] if
                                        d['Name'].startswith('custom')][0]
                })

                user_details_list.append(user_data_dict)

            if not user_data_list:
                message = "Data not found!!"
                response_payload = AppServices.app_response(404, message,
                                                            False,
                                                            [])
                return response_payload

        else:
            message = "Unauthorized, cannot get User " \
                      "details."
            response_payload = AppServices.app_response(403, message, False,
                                                        {})
            return response_payload

        logger.info(
            "user details list status = {}".format(user_details_list))
        message = "User Details list"
        response_payload = AppServices.app_response(200, message, True,
                                                    user_details_list)
        return response_payload

    except Exception as e:
        logger.error(ERROR_FORMAT.format(e.__str__(), "get_user_details"))
        message = "Something went wrong!!"
        response_payload = AppServices.app_response(500, message, False, {})
        return response_payload

# context = "function:dev"
#
# event = {
#     'headers': {
#         'Authorization' '': 'eyJraWQiOiI5c2h2WFNOTWx4QWsyZEhtc1lCZ2lXaWFIOXVKYTZmbUNZNWs0dWdCUlNnPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiJlMzg2Nzg0OC03YjIzLTQyYTUtYWMzMy1iNjQwODk3OTI5YzMiLCJjb2duaXRvOmdyb3VwcyI6WyJVU0VSIiwiQURNSU4iXSwiZW1haWxfdmVyaWZpZWQiOnRydWUsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC51cy1lYXN0LTIuYW1hem9uYXdzLmNvbVwvdXMtZWFzdC0yX29GeWJlcUtEcCIsImNvZ25pdG86dXNlcm5hbWUiOiJlMzg2Nzg0OC03YjIzLTQyYTUtYWMzMy1iNjQwODk3OTI5YzMiLCJvcmlnaW5fanRpIjoiZDE1MzNjMjQtYzFiYy00N2FhLWEyMmItYmI0ZTY4YzBmMWI3IiwiYXVkIjoiMzljdGsxM2lhZHVkdmtiMHBvbThqZ2VvaDMiLCJldmVudF9pZCI6ImZkOTkzY2QxLTIzYzYtNDgzNi1hZWI0LTFmMzExMGZjY2JhZiIsInRva2VuX3VzZSI6ImlkIiwiYXV0aF90aW1lIjoxNjc4MzY0NTI5LCJuYW1lIjoiYWRtaW5AeW9wbWFpbC5jb20iLCJleHAiOjE2NzgzNjgxMjksImlhdCI6MTY3ODM2NDUyOSwianRpIjoiYzY4OTVmMTctZGRiMS00MzZmLWI1NjktNzEzZWQ5YTRmNDQ4IiwiZW1haWwiOiJhZG1pbkB5b3BtYWlsLmNvbSJ9.cFlpsjBMoFSS6b6_HwhiXba0dGUZM4v4MhXNaeYYJ5vXmSI2m0CGsmDGlLvU0pvUrXNnG3sFcg6oxSlB6zCT6is8ESKoIQfxO8ehT-VSl65hyMhYopnFcrDaKLtYivydQyIZqT1AuWJJQtz3GIsOUownGWSqX2g2OMvM3AmBXq7u06b7d0S18prRprhHVUwnvROQbVaa74ncMM8ByZjXXImeSh7sFxf-iVgciMHPhTp7x-TH-sNHRFvkPy5EPn0mZu6QrDccYH46Ei1acduwCi3iRCxuzchKfHtam8TCu2e44tuirWGNAy6giL-v5OX7ikALJmxvkQ1caZN-VB9N8w'
#
#     },
#     "body": {
#         "page_number": 1,
#         "page_size": 10
#     }
#
# }
#
# response_payload = lambda_handler(event, context)
# print(response_payload)
