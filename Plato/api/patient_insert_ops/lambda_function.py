import json
import logging
import time
from configparser import ConfigParser
from datetime import datetime

import json

from config import db_connection
from dao import PatientDAO
from models import PatientVO, Base
from services import AppServices, PlatoServices

logger = logging.getLogger("ksi_plato_patient_operations")
logger.setLevel(logging.INFO)

configure = ConfigParser()
configure.read('config.ini')

date_time = datetime.utcnow().replace(microsecond=0)
current_time = int(time.mktime(date_time.timetuple()))

ERROR_FORMAT = configure.get('ERROR_HANDLING', 'format')

def lambda_handler(event, context):
    logger.info("Params: event = {}".format(event))
    logger.info("Params: context = {}".format(context))
    logger.info("Params: context  type = {}".format(type(context)))
    logger.info("Params: event  type = {}".format(type(event)))
    server_alias = AppServices.get_env(context)
    logger.info("got env = {}".format(server_alias))
    db_engine, session = db_connection(server_alias)
    Base.metadata.create_all(db_engine)

    response = insert_patient_data(event['body'], db_engine, session)
    response_json = json.dumps(response)
    response_json = json.loads(response_json)
    logger.info("response", response_json)
    return response_json


def validate_data(event):
    logger.info("Function: validate_data")
    attributes = ["name", "address", "telephone", "postal", "dial_code"]

    is_valid = True
    for key in attributes:
        if key not in event:
            is_valid = False
        else:
            if not event[key]:
                is_valid = False
            else:
                pass

    return is_valid


def insert_patient_data(event, db_engine, session):
    response = {}
    if type(event) == str:
        event = json.loads(event)

    logger.info("Function: insert_patient_data")
    logger.info("Param: event = {}, db_engine = {}, session = {}".format(
        event, db_engine, session))
    try:
        is_valid = validate_data(event)
        if is_valid:
            patient_vo = PatientVO()
            if event.get('dob'):
                patient_vo.dob = event.get('dob')
            patient_vo.given_id = event.get('given_id')
            patient_vo.name = event.get('name')
            patient_vo.nric = event.get('nric')
            patient_vo.marital_status = event.get('marital_status')
            patient_vo.sex = event.get('sex')
            patient_vo.nationality = event.get('nationality')
            patient_vo.allergies_select = event.get('allergies_select')
            patient_vo.allergies = event.get('allergies')
            patient_vo.nric_type = event.get('nric_type')
            patient_vo.food_allergies_select = event.get(
                'food_allergies_select')
            patient_vo.food_allergies = event.get('food_allergies')
            patient_vo.g6pd = event.get('g6pd')
            patient_vo.dial_code = event.get('dial_code')
            patient_vo.telephone = event.get('telephone')
            patient_vo.alerts = event.get('alerts')
            patient_vo.address = event.get('address')
            patient_vo.postal = event.get('postal')
            patient_vo.unit_no = event.get('unit_no')
            patient_vo.email = event.get('email')
            patient_vo.telephone2 = event.get('telephone2')
            patient_vo.telephone3 = event.get('telephone3')
            patient_vo.title = event.get('title')
            patient_vo.dnd = event.get('dnd')
            patient_vo.occupation = event.get('occupation')
            patient_vo.doctor = event.get('doctor')
            patient_vo.created_on = event.get('created_on')
            patient_vo.created_by = event.get('created_by')
            patient_vo.last_edited = event.get('last_edited')
            patient_vo.last_edited_by = event.get('last_edited_by')
            patient_vo.notes = event.get('notes')
            patient_vo.referred_by = event.get('referred_by')

            PatientDAO.insert_patient(patient_vo, session)
            patient_id = patient_vo.id
            plato_id = PlatoServices.patient_post_api(event)
            update_patient_vo = PatientVO()
            update_patient_vo.id = patient_id
            update_patient_vo.plato_id = plato_id
            PatientDAO.update_patient(update_patient_vo, session)

            response.update({
                "status_code": 200,
                "success": True,
                "message": "patient data insertion & plato api call completed "
                           "successfully",
                "data": {},
                "headers": {
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET"
                },
                "body": json.dumps(response)
            })
        else:
            response.update({
                "status_code": 500,
                "success": False,
                "message": "required parameters not found",
                "data": {},

            })

    except Exception as patient_insert_exec:
        logger.error(ERROR_FORMAT.format(patient_insert_exec.__str__(),
                                         "insert_patient_data"))

        response.update({
            "status_code": 500,
            "success": False,
            "message": "something went wrong",
            "data": {}
        })

    logger.info("response", response)
    return response

# event = {
#     "body": {
#         "given_id": "234234",
#         "name": "a",
#         "nric": "G1234567H",
#         "dob": "2000-5-10",
#         "marital_status": "Married",
#         "sex": "Male",
#         "nationality": "American",
#         "allergies_select": "Yes",
#         "allergies": "Penicillin",
#         "nric_type": "Passport",
#         "food_allergies_select": "Yes",
#         "food_allergies": "lettuce",
#         "g6pd": "No",
#         "dial_code": "99",
#         "telephone": "64712600",
#         "alerts": "Diabetes",
#         "address": "38 ABC Road #09-45/46 Singapore 123456",
#         "postal": "123456",
#         "unit_no": "#09-45/46",
#         "email": "info@example.com",
#         "telephone2": "64712600",
#         "telephone3": "64712600",
#         "title": "Mr",
#         "dnd": "0",
#         "occupation": "Plumber",
#         "doctor": [
#             "DT"
#         ],
#         "notes": "Some notes",
#         "referred_by": ""
#     }
# }
# context = "function:dev"
# res = lambda_handler(event, context)
# print(res)
