from models import TenantDetailsVO


class TenantDetailsDAO:
    @staticmethod
    def insert_tenant_details(tenant_details_vo, session):
        session.add(tenant_details_vo)
        session.commit()

    @staticmethod
    def get_data(tenant_name, session):
        data = session.query(TenantDetailsVO).filter(
            TenantDetailsVO.tenant_name == tenant_name).first()
        return data
