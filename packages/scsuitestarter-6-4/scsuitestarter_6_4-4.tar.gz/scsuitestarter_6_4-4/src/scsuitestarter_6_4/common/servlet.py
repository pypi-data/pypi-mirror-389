import requests


class Servlet:
    """Classe de base d'un servlet accessible hors execframe"""
    def __init__(self, url: str, code: str, session: requests.session):
        self._url: str = f"{url}/{code}"  # url d'appel de la servlet
        self._s: requests.Session = session  # session d'appel au servlet

    def set_session(self, session: requests.Session):
        """Initialisation de la session d'interaction au service"""
        self._s = session
