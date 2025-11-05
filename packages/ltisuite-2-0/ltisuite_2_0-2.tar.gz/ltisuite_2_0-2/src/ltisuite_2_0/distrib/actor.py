from typing import Optional, Any
from ..common.svc import Svc
from ..common.utils import json


class Actor(Svc):
    def transmit_msg(self, actor_id:str, msg:Optional[list[any]]) -> list[Any]:
        return json(self._s.put(self._url, params={"cdaction": "TransmitMsg", "id":actor_id}, json=msg))
