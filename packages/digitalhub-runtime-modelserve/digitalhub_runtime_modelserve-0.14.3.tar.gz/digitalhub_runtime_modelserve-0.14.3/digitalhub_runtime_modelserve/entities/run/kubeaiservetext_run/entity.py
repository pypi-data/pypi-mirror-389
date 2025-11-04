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

    from digitalhub_runtime_modelserve.entities.run.kubeaiservetext_run.spec import RunSpecKubeaiserveTextRun
    from digitalhub_runtime_modelserve.entities.run.kubeaiservetext_run.status import RunStatusKubeaiserveTextRun


class RunKubeaiserveTextRun(RunModelserveRun):
    """
    RunKubeaiserveTextRun class.
    """

    def __init__(
        self,
        project: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: RunSpecKubeaiserveTextRun,
        status: RunStatusKubeaiserveTextRun,
        user: str | None = None,
    ) -> None:
        super().__init__(project, uuid, kind, metadata, spec, status, user)

        self.spec: RunSpecKubeaiserveTextRun
        self.status: RunStatusKubeaiserveTextRun

    def invoke(
        self,
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
            base_url = self.status.service.get("url")
        except AttributeError:
            raise EntityError(
                "Url not specified and service not found on run status."
                " If a service is deploying, use run.wait() or try again later."
            )

        if url is not None and not url.startswith(base_url):
            raise EntityError(f"Invalid URL: {url}. It must start with the service URL: {base_url}")

        if url is None:
            url = self.status.service.get("urls")[0]

        if "data" not in kwargs and "json" not in kwargs:
            method = "GET"

        return requests.request(method=method, url=url, **kwargs)
