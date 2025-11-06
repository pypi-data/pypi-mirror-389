# -*- coding: utf-8 -*-
"""Opencast Assets API."""

import xml.parsers.expat

import requests
from requests.auth import HTTPBasicAuth

from ocpy import OcPyException
from ocpy.api.api_client import OpenCastBaseApiClient
from ocpy.model.mediapackage import MediaPackage


class AssetsApi(OpenCastBaseApiClient):
    """API to manage assets in Opencast."""

    def __init__(self, user=None, password=None, server_url=None, **_kwargs):
        super().__init__(user, password, server_url)
        self.base_url = self.server_url + "/assets"

    def get_episode_mp(self, mp_id, **kwargs) -> MediaPackage:
        res = requests.get(
            self.base_url + "/episode/" + mp_id,
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            **kwargs,
        )
        if res.ok:
            try:
                return MediaPackage(res.text)
            except xml.parsers.expat.ExpatError as exc:
                raise OcPyException(
                    "No valid XML response (probably authentication failure)!"
                ) from exc
        raise OcPyException("Could not get job info!")

    def post_mp_xml(self, mp_xml, **kwargs) -> bool:
        data = {"mediapackage": mp_xml}
        res = requests.post(
            self.base_url + "/add",
            auth=HTTPBasicAuth(self.user, self.password),
            timeout=kwargs.pop("timeout", 30),
            data=data,
        )
        if res.ok:
            return True
        raise OcPyException("Could not post XML!")
