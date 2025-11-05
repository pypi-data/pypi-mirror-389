import xml.etree.ElementTree as ET

from ..common.svc import Svc
from ..common.utils import text


class WspMetaEditor(Svc):
    def get_new_editor(self) -> ET.Element:
        return ET.fromstring(text(self._s.get(self._url, params={"cdaction": "GetNewEditor"})))
