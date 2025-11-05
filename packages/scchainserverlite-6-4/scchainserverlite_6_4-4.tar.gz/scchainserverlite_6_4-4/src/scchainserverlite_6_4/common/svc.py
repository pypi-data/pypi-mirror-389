import requests


class Svc:
    """Classe de base d'un service"""
    def __init__(self, url: str, ef: str, code: str, session: requests.session):
        self._url: str = f"{url}/{ef}/u/{code}"  # url d'appel du service
        self._s = session  # session d'appel au service

    def set_session(self, session: requests.Session):
        """Initialisation de la session d'interaction au service"""
        self._s = session
