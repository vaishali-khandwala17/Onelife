import logging
import time
from configparser import ConfigParser
from datetime import datetime

import requests

from config import db_connection
from dao import SchedulerDAO, PatientDAO
from models import SchedulerVO, PatientVO, Base
from services import AppServices

logger = logging.getLogger("ksi_plato_patient_operations")
logger.setLevel(logging.INFO)

configure = ConfigParser()
configure.read('config.ini')

date_time = datetime.utcnow().replace(microsecond=0)
current_time = int(time.mktime(date_time.timetuple()))

ERROR_FORMAT = configure.get('ERROR_HANDLING', 'format')

API_URL = configure.get('DEV_PLATO_API', 'api_url')
PATIENT_VIEW_URL = configure.get('DEV_PLATO_API', 'patient_view_url')
API_TOKEN = configure.get('DEV_PLATO_API', 'api_token')
PAGE_LIMIT = int(configure.get('DEV_PLATO_API', 'page_limit'))
API_DELAY = float(configure.get('DEV_PLATO_API', 'api_delay'))
SCHEDULER_NAME = configure.get('COMMON_CONFIG', 'scheduler_name')


def lambda_handler(event, context):
    logger.info("Params: event = {}".format(event))
    logger.info("Params: context = {}".format(context))

    server_alias = AppServices.get_env(context)
    logger.info("got env = {}".format(server_alias))

    db_engine, session = db_connection(server_alias)
    Base.metadata.create_all(db_engine)

    response_payload = patient_view_ops(session)
    logger.info("Final response = {}".format(response_payload))

    return response_payload


def patient_view_ops(session):
    logger.info("Function: patient_scheduler_ops")
    try:
        modified_since = None
        scheduler_id = None
        data = SchedulerDAO.get_data(session, SCHEDULER_NAME)
        if data:
            scheduler_id = data.id
            modified_since = data.timestamp

        is_fetch_success = plato_fetch_api(modified_since, session)
        logger.info("is_fetch_success = {}".format(is_fetch_success))

        if not is_fetch_success:
            message = "Something went wrong!!"
            response_payload = AppServices.app_response(500, message, False,
                                                        {})
            return response_payload

        date_time = datetime.utcnow().replace(microsecond=0)
        current_time = int(time.mktime(date_time.timetuple()))
        is_update_success = update_timestamp(scheduler_id, session,
                                             current_time)
        logger.info("is_update_success = {}".format(is_update_success))

        if not is_update_success:
            message = "Something went wrong!!"
            response_payload = AppServices.app_response(500, message, False,
                                                        {})
            return response_payload

        message = "Patient Details insert success"
        response_payload = AppServices.app_response(200, message, True,
                                                    {})
        return response_payload

    except Exception as e:
        logger.info("Function patient_scheduler_ops got error = {}".format(e))
        message = "Something went wrong!!"
        response_payload = AppServices.app_response(500, message, False, {})
        return response_payload


def plato_fetch_api(modified_since, session):
    logger.info("Function: plato_fetch_api")
    logger.info("Params: modified_since = {}".format(modified_since))
    try:
        headers = {'Authorization': "Bearer {}".format(API_TOKEN)}
        api_call = ""
        current_page = 1
        api_flag = True
        while api_flag:
            if modified_since:
                api_call = '{}{}'.format(API_URL, PATIENT_VIEW_URL +
                                         f"current_page={current_page}" +
                                         f"&modified_since={modified_since}")
            else:
                api_call = '{}{}'.format(API_URL,
                                         PATIENT_VIEW_URL +
                                         f"current_page={current_page}")

            api_response = requests.get(api_call, headers=headers).json()
            logger.info(
                "API = {}, API response = {}".format(api_call, api_response))
            current_page = current_page + 1
            if api_response:
                time.sleep(API_DELAY)
                for patient_data in api_response:
                    is_insert = patient_insert_db(patient_data, session)
                    logger.info("patient_data = {}, is_insert = {}".format(
                        patient_data, is_insert))
            else:
                api_flag = False
                break

        return True

    except Exception as e:
        logger.info("Function plato_fetch_api got error = {}".format(e))
        return False


def patient_insert_db(patient_data, session):
    logger.info("Function: patient_insert_db")
    logger.info("Param: patient_data = {}".format(patient_data))
    try:
        patient_vo = PatientVO()
        plato_id = patient_data.get('_id')
        if patient_data.get('dob') != '0000-00-00':
            patient_vo.dob = patient_data.get('dob')
        patient_vo.given_id = patient_data.get('given_id')
        patient_vo.name = patient_data.get('name')
        patient_vo.nric = patient_data.get('nric')
        patient_vo.marital_status = patient_data.get('marital_status')
        patient_vo.sex = patient_data.get('sex')
        patient_vo.nationality = patient_data.get('nationality')
        patient_vo.allergies_select = patient_data.get('allergies_select')
        patient_vo.allergies = patient_data.get('allergies')
        patient_vo.nric_type = patient_data.get('nric_type')
        patient_vo.food_allergies_select = patient_data.get(
            'food_allergies_select')
        patient_vo.food_allergies = patient_data.get('food_allergies')
        patient_vo.g6pd = patient_data.get('g6pd')
        patient_vo.dial_code = patient_data.get('dial_code', "")
        patient_vo.telephone = patient_data.get('telephone')
        patient_vo.alerts = patient_data.get('alerts')
        patient_vo.address = patient_data.get('address')
        patient_vo.postal = patient_data.get('postal')
        patient_vo.email = patient_data.get('email')
        patient_vo.telephone2 = patient_data.get('telephone2')
        patient_vo.telephone3 = patient_data.get('telephone3')
        patient_vo.title = patient_data.get('title')
        patient_vo.dnd = patient_data.get('dnd')
        patient_vo.occupation = patient_data.get('occupation')
        patient_vo.doctor = patient_data.get('doctor')
        patient_vo.created_on = patient_data.get('created_on')
        patient_vo.created_by = patient_data.get('created_by')
        patient_vo.last_edited = patient_data.get('last_edited')
        patient_vo.last_edited_by = patient_data.get('last_edited_by')
        patient_vo.notes = patient_data.get('notes')
        patient_vo.referred_by = patient_data.get('referred_by')
        patient_vo.plato_id = patient_data.get('_id')

        data = PatientDAO.patient_get_data(plato_id, session)
        if data:
            patient_vo.id = data.id
            PatientDAO.update_patient(patient_vo, session)
        else:
            SchedulerDAO.insert_patient(patient_vo, session)
        return True

    except Exception as e:
        logger.error("Function patient_insert_db got error = {}".format(e))
        return False


def update_timestamp(scheduler_id, session, current_time):
    logger.info("Function: update_timestamp")
    logger.info(
        "Params: scheduler_id = {}, session = {}, current_time ={}".format(
            scheduler_id, session, current_time))
    try:
        update_vo = SchedulerVO()
        if scheduler_id:
            update_vo.id = scheduler_id
            update_vo.timestamp = current_time
            update_vo.scheduler_name = SCHEDULER_NAME
            SchedulerDAO.update(update_vo, session)
        else:
            update_vo.timestamp = current_time
            update_vo.scheduler_name = SCHEDULER_NAME
            SchedulerDAO.insert_scheduler(update_vo, session)
        return True

    except Exception as e:
        logger.error("Function update_timestamp got error = {}".format(e))
        return False

# context = "function:dev"
# event = {}
# response = lambda_handler(event, context)
# print(response)
