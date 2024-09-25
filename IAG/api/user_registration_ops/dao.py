from models import RegistrationOtpHistoryVO, UserDetailsVO, TenantDetailsVO


class UserDetailsDAO:
    @staticmethod
    def insert_user_details(user_details_vo, session):
        session.add(user_details_vo)
        session.commit()

    @staticmethod
    def get_otp(session, username):
        data = session.query(UserDetailsVO).filter(
            UserDetailsVO.username == username).first()
        return data



class RegistrationOtpHistoryDAO:
    @staticmethod
    def get_user_details(session, username, user_request_id):
        data = session.query(RegistrationOtpHistoryVO) \
            .filter(RegistrationOtpHistoryVO.username == username) \
            .filter(
            RegistrationOtpHistoryVO.user_request_id == user_request_id) \
            .first()
        return data

    @staticmethod
    def update_user_status(user_vo, session):
        session.merge(user_vo)
        session.commit()

    @staticmethod
    def get_tenant(session, tenant_name):
        data = session.query(TenantDetailsVO).filter(
            TenantDetailsVO.tenant_name == tenant_name).first()
        return data

class TenantDetailsDAO:

    @staticmethod
    def get_data(tenant_secret_id, tenant_secret_key, session):
        data = session.query(TenantDetailsVO)\
            .filter(
            TenantDetailsVO.tenant_secret_id == tenant_secret_id) \
            .filter(
            TenantDetailsVO.tenant_secret_key == tenant_secret_key) \
            .first()
        return data