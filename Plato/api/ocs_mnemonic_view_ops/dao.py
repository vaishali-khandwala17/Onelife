from models import MnemonicVO
from sqlalchemy import or_


class MnemonicDAO:
    @staticmethod
    def get_data(session, search_value):
        if not search_value:
            data = session.query(MnemonicVO).limit(500).all()
        else:
            search_value = '%{}%'.format(search_value)
            data = session.query(MnemonicVO) \
                .filter(or_(MnemonicVO.mnemonic.ilike(search_value),
                            MnemonicVO.commercial_name.ilike(search_value))) \
                .limit(500).all()
        return data
