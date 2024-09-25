from models import RegistrationOtpHistoryVO, TenantDetailsVO


class RegistrationOtpHistoryDAO:
    @staticmethod
    def get_user_details(session, username, user_request_id):
        data = session.query(RegistrationOtpHistoryVO) \
            .filter(RegistrationOtpHistoryVO.username == username) \
            .filter(
            RegistrationOtpHistoryVO.user_request_id == user_request_id) \
            .first()
        return data


class TenantDetailsDAO:

    @staticmethod
    def get_data(tenant_secret_id, tenant_secret_key, session):
        data = session.query(TenantDetailsVO) \
            .filter(
            TenantDetailsVO.tenant_secret_id == tenant_secret_id) \
            .filter(
            TenantDetailsVO.tenant_secret_key == tenant_secret_key) \
            .first()
        return data


class UserOtpHistoryDAO:
    @staticmethod
    def update_otp_history(user_otp_history_vo, session):
        session.merge(user_otp_history_vo)
        session.commit()
