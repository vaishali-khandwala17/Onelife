from models import DailyDoseMasterVO
from sqlalchemy import or_


class DailyDoseMasterDAO:
    @staticmethod
    def get_data(session, search_value):
        if not search_value:
            data = session.query(DailyDoseMasterVO).limit(500).all()
        else:
            search_value = '%{}%'.format(search_value)
            data = session.query(DailyDoseMasterVO) \
                .filter(
                or_(DailyDoseMasterVO.dose_abbreviation.ilike(search_value),
                    DailyDoseMasterVO.return_value.ilike(search_value))) \
                .limit(500).all()
        return data
