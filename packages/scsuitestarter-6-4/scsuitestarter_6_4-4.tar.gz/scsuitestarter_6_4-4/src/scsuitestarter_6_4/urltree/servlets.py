import requests

from ..common.servlet import Servlet
from ..common.utils import json, check_status, text


class UrlTreeRenderer(Servlet):
	def __call__(self, *args: str, allow_redirects=False):
		if len(args) == 0:
			return self._s.get(f"{self._url}")
		elif len(args) == 1:
			return self._s.get(f"{self._url}{args[0]}")

		elif args[1] == "nodeInfos":
			return json(self._s.get(f"{self._url}{args[0]}", params={"nodeInfos": ""}, allow_redirects=allow_redirects))
		elif args[1] == "listChildren":
			return json(self._s.get(f"{self._url}{args[0]}", params={"listChildren": ""}, allow_redirects=allow_redirects))
		elif args[1] == "searchNodes":
			return json(self._s.get(f"{self._url}{args[0]}", params={"searchNodes": ""}, allow_redirects=allow_redirects))
		elif args[1] == "infoViews":
			return json(self._s.get(f"{self._url}{args[0]}", params={"infoViews": ""}, allow_redirects=allow_redirects))
		elif args[1] == "userRolesMap":
			return json(self._s.get(f"{self._url}{args[0]}", params={"userRolesMap": ""}, allow_redirects=allow_redirects))
		elif args[1] == "view":
			return json(self._s.get(f"{self._url}{args[0]}", params={"view": ""}, allow_redirects=allow_redirects))
		elif args[1] == "treePath":
			return text(self._s.get(f"{self._url}{args[0]}", params={"treePath": ""}, allow_redirects=allow_redirects))
		elif args[1] == "permaLink":
			return text(self._s.get(f"{self._url}{args[0]}", params={"permaLink": ""}, allow_redirects=allow_redirects))
		elif args[1] == "gotoTags":
			return self._s.get(f"{self._url}{args[0]}", params={"gotoTags": args[2]}, allow_redirects=allow_redirects).content
		elif args[1] == "searchTags":
			return json(self._s.get(f"{self._url}{args[0]}", params={"searchTags": args[2]}, allow_redirects=allow_redirects))
		elif args[1] == "download":
			return self._s.get(f"{self._url}{args[0]}", params={"download": ""}, allow_redirects=allow_redirects).content

		elif args[1] == "json":
			return json(self._s.get(f"{self._url}{args[0]}", allow_redirects=allow_redirects))
		elif args[1] == "status":
			return self._s.get(f"{self._url}{args[0]}", allow_redirects=allow_redirects).status_code
		elif args[1] == "text":
			return text(self._s.get(f"{self._url}{args[0]}", allow_redirects=allow_redirects))
		elif args[1] == "bytes":
			return self._s.get(f"{self._url}{args[0]}", allow_redirects=allow_redirects).content

		else:
			raise ValueError(f"Unable to call UrlTreeRenderer with args {args} arg.")


class UrlTreeEsSearchServlet(Servlet):
	def __init__(self, url: str, code: str, session: requests.session, index: str = "depot"):
		super().__init__(url, code, session)
		self.index: str = index

	def __call__(self, query=None, index=None):
		idx = index if index is not None else self.index
		if query is None:
			resp = self._s.get(f"{self._url}/{idx}/_search")

		else:
			resp = self._s.post(f"{self._url}/{idx}/_search", json=query)
		check_status(resp, 200)
		return json(resp)
