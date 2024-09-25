import logging
from configparser import ConfigParser

import boto3

from config import db_connection
from dao import TenantDetailsDAO
from models import Base
from services import AppServices

logger = logging.getLogger("ksi_tenant_listing_operations")
logger.setLevel(logging.INFO)

cognito_client = boto3.client('cognito-idp')

configure = ConfigParser()
configure.read('config.ini')

USER_POOL_ID = configure.get('COGNITO_CONFIG', 'user_pool_id')
ERROR_FORMAT = configure.get('ERROR_HANDLING', 'format')


def validate_request(request_data):
    logger.info("Function validate_request")
    logger.info("params: request_data = {}".format(request_data))
    attributes = ["page_number", "page_size"]
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

    admin_username = event["headers"]["name"]
    admin_group_response = cognito_client.admin_list_groups_for_user(
        UserPoolId=USER_POOL_ID,
        Username=admin_username
    )
    logger.info("admin_group_response = {}".format(admin_group_response))
    user_groups = [group['GroupName'] for group in
                   admin_group_response['Groups']]
    if "ADMIN" not in user_groups:
        message = "Unauthorized, only admin can get Tenant details."
        response_payload = AppServices.app_response(403, message, False, {})
        return response_payload

    request_data = event["body"]
    is_valid, attribute = validate_request(request_data)

    if not is_valid:
        message = "{} parameter missing or invalid.".format(attribute)
        response_payload = AppServices.app_response(400, message, False,
                                                    {})
        return response_payload

    response_payload = get_tenant_details(request_data, session)
    logger.info("final response_payload = {}".format(response_payload))
    return response_payload


def get_tenant_details(request_data, session):
    logger.info("function:tenant_details")
    logger.info("Params: event = {}".format(request_data))
    try:
        page_number = int(request_data["page_number"])
        limit = int(request_data["page_size"])
        skip = (page_number - 1) * limit
        search_value = request_data.get("search_value", None)

        tenant_details_data_list = TenantDetailsDAO.get_tenant_data(
            session, skip, limit, search_value)

        if not tenant_details_data_list:
            message = "Data not found!!"
            response_payload = AppServices.app_response(404, message, False,
                                                        [])
            return response_payload

        tenant_details_list = []

        for tenant_details in tenant_details_data_list:
            tenant_details_list.append(tenant_details.to_dict())

        logger.info(
            "tenant details list status = {}".format(tenant_details_list))
        message = "Tenant Details list"
        response_payload = AppServices.app_response(200, message, True,
                                                    tenant_details_list)
        return response_payload

    except Exception as e:
        logger.error(ERROR_FORMAT.format(e.__str__(), "tenant_details"))
        message = "Something went wrong!!"
        response_payload = AppServices.app_response(500, message, False, {})
        return response_payload

# context = "function:dev"
# event = {"page_number": 1, "page_size": 10}
# response_payload = lambda_handler(event, context)
# print(response_payload)
