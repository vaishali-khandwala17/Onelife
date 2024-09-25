from models import RegistrationOtpHistoryVO, TenantDetailsVO


class RegistrationOtpHistoryDAO:
    @staticmethod
    def insert_registration_otp_history(registration_otp_history_vo, session):
        session.add(registration_otp_history_vo)
        session.commit()

    @staticmethod
    def get_data(username, session):
        data = session.query(RegistrationOtpHistoryVO).filter(
            RegistrationOtpHistoryVO.username == username).first()
        return data

    @staticmethod
    def update(update_vo, session):
        session.merge(update_vo)
        session.commit()


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

    @staticmethod
    def get_tenant(session, tenant_name):
        data = session.query(TenantDetailsVO).filter(
            TenantDetailsVO.tenant_name == tenant_name).first()
        return data