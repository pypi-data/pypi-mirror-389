from typing import Optional, Any
from ..common.svc import Svc
from ..common.utils import json


class Participant(Svc):
    def transmit_msg(self, participant_id:str, msg:Optional[list[any]]) -> list[Any]:
        return json(self._s.put(self._url, params={"cdaction": "TransmitMsg", "id":participant_id}, json=msg))
