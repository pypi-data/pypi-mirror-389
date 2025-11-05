# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

import requests
from digitalhub.utils.exceptions import EntityError

from digitalhub_runtime_modelserve.entities.run.modelserve_run.entity import RunModelserveRun

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata

    from digitalhub_runtime_modelserve.entities.run.huggingfaceserve_run.spec import RunSpecHuggingfaceserveRun
    from digitalhub_runtime_modelserve.entities.run.huggingfaceserve_run.status import RunStatusHuggingfaceserveRun


class RunHuggingfaceserveRun(RunModelserveRun):
    """
    RunHuggingfaceserveRun class.
    """

    def __init__(
        self,
        project: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: RunSpecHuggingfaceserveRun,
        status: RunStatusHuggingfaceserveRun,
        user: str | None = None,
    ) -> None:
        super().__init__(project, uuid, kind, metadata, spec, status, user)

        self.spec: RunSpecHuggingfaceserveRun
        self.status: RunStatusHuggingfaceserveRun

    def invoke(
        self,
        model_name: str | None = None,
        method: str = "POST",
        url: str | None = None,
        **kwargs,
    ) -> requests.Response:
        """
        Invoke served model. By default it exposes infer v2 endpoint.

        Parameters
        ----------
        model_name : str
            Name of the model.
        method : str
            Method of the request.
        url : str
            URL of the request.
        **kwargs : dict
            Keyword arguments to pass to the request.

        Returns
        -------
        requests.Response
            Response from the request.
        """
        try:
            base_url: str = self.status.service.get("url")
        except AttributeError:
            raise EntityError(
                "Url not specified and service not found on run status."
                " If a service is deploying, use run.wait() or try again later."
            )

        if url is not None and not url.removeprefix("http://").removeprefix("https://").startswith(base_url):
            raise EntityError(f"Invalid URL: {url}. It must start with the service URL: {base_url}")

        if url is None:
            model_name = model_name if model_name is not None else "model"
            url = f"http://{base_url}/v2/models/{model_name}/infer"

        if "data" not in kwargs and "json" not in kwargs:
            method = "GET"

        return requests.request(method=method, url=url, **kwargs)
