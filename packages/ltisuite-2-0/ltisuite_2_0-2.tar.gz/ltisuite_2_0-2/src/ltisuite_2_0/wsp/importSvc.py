from typing import Optional

from ..common import utils
from ..common.svc import Svc


class Import(Svc):

    def import_archive(self, wsp_code: str, content: bytes | str, ref_uri_target: Optional[str] = None, replace_if_exist: bool = True) -> None:
        """
        Importe un scar/scwsp dans un atelier existant
        :param wsp_code: atelier dans lequel importer
        :param content: byte ou path d"un fichier à importer
        :param ref_uri_target: refUri dans lequel importer les ressources
        :param replace_if_exist: si True, remplacera les ressources existantes si elles existent déjà
        """
        if content is str:
            with open(content, "rb") as file:
                data = file.read()
        else:
            data = content
        qs = {"cdaction": "Import", "wspTarget": wsp_code}

        if ref_uri_target is not None:
            qs["refUriTarget"] = ref_uri_target

        if replace_if_exist is not None:
            qs["replaceIfExist"] = replace_if_exist

        utils.check_status(self._s.put(self._url, params=qs, data=data), 200)
