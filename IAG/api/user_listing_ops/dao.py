from models import UserDetailsVO, TenantDetailsVO,RegistrationOtpHistoryVO


class UserDetailsDAO:
    @staticmethod
    def get_user_data(session, skip, limit, search_value):
        if search_value:
            data = session.query(UserDetailsVO) \
                .filter(UserDetailsVO.tenant_id == search_value) \
                .offset(skip).limit(limit).all()
        else:
            data = session.query(UserDetailsVO).offset(skip).limit(limit).all()
        return data

    @staticmethod
    def get_data(session, skip, limit, username):
        data = session.query(UserDetailsVO).filter(UserDetailsVO.username ==
                                                   username).offset(
            skip).limit(limit).all()
        return data

    @staticmethod
    def get_tenant_id(session, username):
        data = session.query(UserDetailsVO).filter(UserDetailsVO.username
                                                   == username).first()
        return data

    @staticmethod
    def get_tenant_user_data(session, tenant_id, skip, limit):
        data = session.query(UserDetailsVO).filter(UserDetailsVO.tenant_id
                                                   == tenant_id).offset(
            skip).limit(
            limit).all()
        return data

class TenantDetailsDAO:
    @staticmethod
    def get_tenant_name(session, tenant_id):
        data = session.query(TenantDetailsVO).filter(TenantDetailsVO.id
                                                     == tenant_id).first()
        return data

    @staticmethod
    def get_tenant_data(session, username):
        data = session.query(TenantDetailsVO).filter(TenantDetailsVO.username
                                                     == username).first()
        return data

class RegistrationOtpHistoryDAO:
    @staticmethod
    def get_user_data (session,skip,limit,search_value):
        if search_value:
            data = session.query(RegistrationOtpHistoryVO) \
                .filter(RegistrationOtpHistoryVO.tenant_id == search_value) \
                .offset(skip).limit(limit).all()
        else:
            data = session.query(RegistrationOtpHistoryVO).offset(
                skip).limit(limit).all()
        return data