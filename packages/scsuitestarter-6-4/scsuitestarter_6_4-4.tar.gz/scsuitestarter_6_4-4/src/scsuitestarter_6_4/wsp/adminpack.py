from typing import Optional, Any, TypedDict
from ..common.svc import Svc
from ..common.utils import StrEnum, json


class EWspPackStatus(StrEnum):
    uploadPending = "uploadPending"
    installPending = "installPending"
    installed = "installed"
    installFailed = "installFailed"


class EWspPackErrors(StrEnum):
    unknownError = "unknownError"
    versionPackUnknown = "versionPackUnknown"
    versionFrameworkPackOutdated = "versionFrameworkPackOutdated"
    versionServerOutdated = "versionServerOutdated"
    malformedPack = "malformedPack"


class JPackBase(TypedDict):
    id: str
    title: Optional[str]
    buildId: Optional[str]
    installStatus: Optional[EWspPackStatus]


class JWspPackBase(JPackBase):
    error: Optional[EWspPackErrors]


class JWspPackInstalled(JWspPackBase):
    system: Optional[bool]
    installDate: Optional[int]
    wspTypeDef: Any
    framework: Any


class AdminPack(Svc):
    def list_packs(self) -> list[JWspPackInstalled | JWspPackBase]:
        return json(self._s.get(self._url, params={"cdaction": "ListPacks"}))

    def install_pack(self, pack: bytes | str, sync: bool = True) -> JPackBase:
        if pack is str:
            with open(pack, "rb") as file:
                data = file.read()
        else:
            data = pack
        return json(self._s.put(self._url, params={"cdaction": "InstallPack", "sync": "true" if sync else "false"}, data=data))["pack"]
