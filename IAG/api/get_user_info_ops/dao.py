from models import UserDetailsVO


class UserDetailsDAO:
    @staticmethod
    def get_data(username, session):
        data = session.query(UserDetailsVO).filter(
            UserDetailsVO.username == username).first()
        return data