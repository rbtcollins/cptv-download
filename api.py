from apibase import APIBase

import json
import requests
from urllib.parse import urljoin


class API(APIBase):
    def __init__(self, baseurl, username, password):
        super().__init__(baseurl, username, password, "user")

    def query(
        self,
        type_=None,
        startDate=None,
        endDate=None,
        min_secs=None,
        limit=100,
        offset=0,
        tagmode=None,
        tags=None,
        devices=None,
    ):
        url = urljoin(self._baseurl, "/api/v1/recordings")

        where = {}
        if type_ is not None:
            where["type"] = type_
        if min_secs is not None:
            where["duration"] = {"$gte": min_secs}
        if startDate is not None:
            where["recordingDateTime"] = {"$gte": startDate.isoformat()}
        if endDate is not None:
            where.setdefault("recordingDateTime", {})["$lte"] = endDate.isoformat()
        if devices is not None:
            where["DeviceId"] = devices
        params = {"where": json.dumps(where)}

        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if tagmode is not None:
            params["tagMode"] = tagmode
        if tags is not None:
            params["tags"] = json.dumps(tags)

        r = requests.get(url, params=params, headers=self._auth_header)
        if r.status_code == 200:
            return r.json()["rows"]
        if r.status_code in (400, 422):
            messages = r.json()["message"]
            raise IOError("request failed ({}): {}".format(r.status_code, messages))
        return r.raise_for_status()

    def download(self, recording_id):
        return self._download_recording(recording_id, "downloadFileJWT")

    def download_raw(self, recording_id):
        return self._download_recording(recording_id, "downloadRawJWT")

    def _download_recording(self, recording_id, jwt_key):
        url = urljoin(self._baseurl, "/api/v1/recordings/{}".format(recording_id))
        r = requests.get(url, headers=self._auth_header)
        d = self._check_response(r)
        return self._download_signed(d[jwt_key])

    def _download_signed(self, token):
        r = requests.get(
            urljoin(self._baseurl, "/api/v1/signedUrl"),
            params={"jwt": token},
            stream=True,
        )
        r.raise_for_status()
        yield from r.iter_content(chunk_size=4096)
