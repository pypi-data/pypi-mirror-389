from ..common.svc import Svc
from ..common.utils import check_status


class ActlogJson(Svc):
    def purge_old_logs(self, days_to_keep: int = 365):
        check_status(self._s.post(self._url, params={"cdaction": "PurgeOldLogs", "param": days_to_keep}), 200)
