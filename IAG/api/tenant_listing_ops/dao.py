from models import TenantDetailsVO


class TenantDetailsDAO:
    @staticmethod
    def get_tenant_data(session, skip, limit, search_value):
        if search_value:
            search_value = '%{}%'.format(search_value)
            data = session.query(TenantDetailsVO) \
                .filter(TenantDetailsVO.tenant_name.ilike(search_value)) \
                .offset(skip).limit(limit).all()
        else:
            data = session.query(TenantDetailsVO) \
                .offset(skip).limit(limit).all()
        return data
