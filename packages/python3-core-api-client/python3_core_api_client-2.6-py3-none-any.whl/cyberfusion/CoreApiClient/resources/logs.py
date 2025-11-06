from cyberfusion.CoreApiClient import models
from typing import Optional

from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse
from cyberfusion.CoreApiClient.interfaces import Resource


class Logs(Resource):
    def list_access_logs(
        self,
        *,
        virtual_host_id: int,
        timestamp: Optional[str] = None,
        sort: Optional[str] = None,
        page: int = 1,
    ) -> DtoResponse[list[models.WebServerLogAccessResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/logs/access/{virtual_host_id}",
            data=None,
            query_parameters={
                "timestamp": timestamp,
                "page": page,
            },
        )

        return DtoResponse.from_response(
            local_response, models.WebServerLogAccessResource
        )

    def list_error_logs(
        self,
        *,
        virtual_host_id: int,
        timestamp: Optional[str] = None,
        sort: Optional[str] = None,
        page: int = 1,
    ) -> DtoResponse[list[models.WebServerLogErrorResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/logs/error/{virtual_host_id}",
            data=None,
            query_parameters={
                "timestamp": timestamp,
                "page": page,
            },
        )

        return DtoResponse.from_response(
            local_response, models.WebServerLogErrorResource
        )

    def list_object_logs(
        self,
        *,
        page: int = 1,
        per_page: int = 0,
        include_filters: models.ObjectLogsSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.ObjectLogResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/object-logs",
            data=None,
            query_parameters={
                "page": page,
                "per_page": per_page,
            }
            | (include_filters.dict(exclude_unset=True) if include_filters else {})
            | construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.ObjectLogResource)

    def list_request_logs(
        self,
        *,
        page: int = 1,
        per_page: int = 0,
        include_filters: models.RequestLogsSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.RequestLogResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/request-logs",
            data=None,
            query_parameters={
                "page": page,
                "per_page": per_page,
            }
            | (include_filters.dict(exclude_unset=True) if include_filters else {})
            | construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.RequestLogResource)
