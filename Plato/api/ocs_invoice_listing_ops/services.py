import logging
import configparser

configure = configparser.ConfigParser()
configure.read('config.ini')

logger = logging.getLogger("ksi_plato_invoice_listing_operations")
logger.setLevel(logging.INFO)

ERROR_FORMAT = configure.get('ERROR_HANDLING', 'format')


class AppServices:

    def __init__(self):
        self.region_name = "us-east-2"

    @staticmethod
    def get_env(context):
        split_arn = context.invoked_function_arn.split(':')
        # split_arn = context.split(':')
        env = split_arn[len(split_arn) - 1]
        env_list = ['dev', 'qa', 'prod']
        return env if env in env_list else 'dev'

    @staticmethod
    def app_response(status_code: int, message: str, success: bool = None,
                     data: any = None) -> dict:
        response = {
            "status_code": status_code,
            "success": success,
            "message": message,
            "data": data
        }
        return response
