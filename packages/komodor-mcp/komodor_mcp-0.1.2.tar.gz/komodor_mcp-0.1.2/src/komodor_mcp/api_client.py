"""Simple Komodor API client wrapper using the generated client library."""

from typing import Any, Literal

import structlog
from mcp.server.fastmcp import FastMCP
from openapi_client import ApiClient
from openapi_client.api.api_key_api import ApiKeyApi
from openapi_client.api.clusters_api import ClustersApi
from openapi_client.api.events_api import EventsApi
from openapi_client.api.health_risks_api import HealthRisksApi
from openapi_client.api.issues_api import IssuesApi
from openapi_client.api.jobs_api import JobsApi
from openapi_client.api.klaudia_api import KlaudiaApi
from openapi_client.api.komodor_cost_api import KomodorCostApi
from openapi_client.api.services_api import ServicesApi
from openapi_client.models.check_category import CheckCategory
from openapi_client.models.check_type import CheckType

# Import response types
from openapi_client.models.clusters_response import ClustersResponse
from openapi_client.models.cost_right_sizing_per_container_response import (
    CostRightSizingPerContainerResponse,
)
from openapi_client.models.cost_right_sizing_per_service_response import (
    CostRightSizingPerServiceResponse,
)
from openapi_client.models.get_all_health_risks_response import (
    GetAllHealthRisksResponse,
)
from openapi_client.models.get_violation_response import GetViolationResponse
from openapi_client.models.impact_group_identifier import ImpactGroupIdentifier
from openapi_client.models.impact_group_type import ImpactGroupType
from openapi_client.models.klaudia_rca_request import KlaudiaRcaRequest
from openapi_client.models.klaudia_rca_response import KlaudiaRcaResponse
from openapi_client.models.klaudia_rca_results_response import KlaudiaRcaResultsResponse
from openapi_client.models.optional_cluster_scope import OptionalClusterScope
from openapi_client.models.pagination_params import PaginationParams

# Import body and scope types
from openapi_client.models.search_services_body import SearchServicesBody
from openapi_client.models.search_services_response import SearchServicesResponse

# Import parameter types
from openapi_client.models.service_kind import ServiceKind
from openapi_client.models.severity import Severity
from openapi_client.models.violation_status import ViolationStatus

from .config import config

logger = structlog.get_logger(__name__)


class KomodorClient:
    """Simple Komodor API client wrapper with proper typing and individual parameters."""

    def __init__(self, headers: dict[str, str] | None = None):
        headers_with_ua = (headers or {}).copy()
        headers_with_ua["User-Agent"] = "komodor/mcp"

        self.client = ApiClient()
        self.client.configuration.host = config.KOMODOR_API_BASE_URL
        self.client.configuration.timeout = 30.0
        self.client.default_headers.update(headers_with_ua)

        # Initialize API clients
        self.services_api = ServicesApi(self.client)
        self.events_api = EventsApi(self.client)
        self.issues_api = IssuesApi(self.client)
        self.jobs_api = JobsApi(self.client)
        self.health_risks_api = HealthRisksApi(self.client)
        self.klaudia_api = KlaudiaApi(self.client)
        self.komodor_cost_api = KomodorCostApi(self.client)
        self.api_key_api = ApiKeyApi(self.client)
        self.clusters_api = ClustersApi(self.client)

    def with_auth(self, mcp: FastMCP) -> "KomodorClient":
        """Create a new client instance with authentication headers."""
        request = mcp.get_context().request_context.request
        if request is None:
            raise ValueError("Request context is required")
        api_key = request.headers.get("Authorization") or request.headers.get(
            "X-API-Key"
        )
        if "Bearer" in api_key:
            api_key = api_key.split(" ")[1]
        if not api_key:
            raise ValueError("API key required in headers")

        headers = {"X-API-Key": api_key, "User-Agent": "komodor/mcp"}
        return KomodorClient(headers)

    async def close(self) -> None:
        """Close the HTTP client session to prevent resource leaks."""
        if hasattr(self.client, "rest_client") and hasattr(
            self.client.rest_client, "close"
        ):
            await self.client.rest_client.close()

    async def __aenter__(self) -> "KomodorClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        await self.close()

    # Clusters
    async def get_clusters(
        self, cluster_name: list[str] | None = None, tags: list[str] | None = None
    ) -> ClustersResponse:
        """Get list of all clusters with optional filtering."""
        return await self.clusters_api.api_v2_clusters_get(
            cluster_name=cluster_name, tags=tags
        )

    # Services
    async def search_services(
        self,
        cluster: str | None = None,
        namespaces: list[str] | None = None,
        service_kind: list[ServiceKind] | None = None,
        status: Literal["healthy", "unhealthy"] = "unhealthy",
        page_size: int | None = None,
        page: int | None = None,
    ) -> SearchServicesResponse:
        """Search for services with individual parameters."""
        # Create search body with individual parameters
        body = SearchServicesBody()

        # Add scope if provided
        if cluster or namespaces:
            scope = OptionalClusterScope(cluster=cluster, namespaces=namespaces)
            body.scope = scope

        # Add service kind filter if provided
        if service_kind:
            body.kind = service_kind

        # Add status filter if provided
        if status:
            body.status = status

        # Add pagination if provided
        if page_size or page:
            pagination = PaginationParams()
            if page_size:
                pagination.page_size = page_size
            if page:
                pagination.page = page
            body.pagination = pagination

        return await self.services_api.api_v2_services_search_post(
            search_services_body=body
        )

    async def get_service_yaml(
        self, cluster: str, namespace: str, kind: ServiceKind, name: str
    ) -> Any:
        """Get service YAML configuration."""
        return await self.services_api.api_v2_service_yaml_get(
            cluster=cluster,
            namespace=namespace,
            kind=kind,
            name=name,
        )

    # Health Risks
    async def get_health_risks(
        self,
        page_size: int,
        offset: int,
        impact_group_type: list[ImpactGroupType],
        check_type: list[CheckType] | None = None,
        status: list[ViolationStatus] | None = None,
        cluster_name: list[str] | None = None,
        namespace: list[str] | None = None,
        short_resource_name_search_term: str | None = None,
        short_resource_name: list[str] | None = None,
        impact_group_id: list[ImpactGroupIdentifier] | None = None,
        severity: list[Severity] | None = None,
        komodor_uid: list[str] | None = None,
        resource_type: list[str] | None = None,
        created_from_epoch: str | None = None,
        created_to_epoch: str | None = None,
        check_category: list[CheckCategory] | None = None,
    ) -> GetAllHealthRisksResponse:
        """Get health risks with individual parameters."""
        return await self.health_risks_api.get_health_risks(
            page_size=page_size,
            offset=offset,
            check_type=check_type,
            status=status,
            cluster_name=cluster_name,
            namespace=namespace,
            short_resource_name_search_term=short_resource_name_search_term,
            short_resource_name=short_resource_name,
            impact_group_id=impact_group_id,
            impact_group_type=impact_group_type,
            severity=severity,
            komodor_uid=komodor_uid,
            resource_type=resource_type,
            created_from_epoch=created_from_epoch,
            created_to_epoch=created_to_epoch,
            check_category=check_category,
        )

    async def get_health_risk_data(self, risk_id: str) -> GetViolationResponse:
        """Get detailed health risk data."""
        return await self.health_risks_api.get_health_risk_data(id=risk_id)

    # Klaudia RCA
    async def trigger_klaudia_rca(
        self,
        cluster: str,
        namespace: str,
        resource_kind: str,
        resource_name: str,
    ) -> KlaudiaRcaResponse:
        """Trigger Klaudia RCA investigation with individual parameters."""
        body = KlaudiaRcaRequest(
            kind=resource_kind,
            name=resource_name,
            namespace=namespace,
            clusterName=cluster,
        )
        return await self.klaudia_api.trigger_klaudia_rca(klaudia_rca_request=body)

    async def get_klaudia_rca_results(
        self, session_id: str
    ) -> KlaudiaRcaResultsResponse:
        """Get Klaudia RCA results."""
        return await self.klaudia_api.get_klaudia_rca_results(id=session_id)

    # Cost Analysis
    async def get_cost_right_sizing_per_service(
        self,
        cluster_scope: list[str],
        service: str,
        optimization_strategy: (
            Literal["conservative", "moderate", "aggressive"] | None
        ) = None,
    ) -> CostRightSizingPerServiceResponse:
        """Get cost right-sizing recommendations per service."""

        return await self.komodor_cost_api.get_cost_right_sizing_per_service(
            cluster_scope=cluster_scope,
            page_size=100,
            filter_by="komodorServiceName",
            filter_value_equals=service,
            sort_order="desc",
            sort_by="potentialSaving",
            optimization_strategy=optimization_strategy,  # type: ignore
        )

    async def get_cost_right_sizing_per_container(
        self,
        cluster: str,
        namespace: str,
        service_kind: str,
        service_name: str,
    ) -> CostRightSizingPerContainerResponse:
        """Get cost right-sizing recommendations per container."""
        return await self.komodor_cost_api.get_cost_right_sizing_per_container(
            cluster_name=cluster,
            namespace=namespace,
            service_kind=service_kind,
            service_name=service_name,
        )

    # Health Check
    async def health_check(self) -> bool:
        """Check if API is accessible."""
        try:
            await self.api_key_api.api_keys_controller_validate()
            return True
        except Exception:
            return False


def create_authenticated_client(mcp: FastMCP) -> KomodorClient:
    """Create a new authenticated client instance from MCP context.

    This is a standalone function that can be imported and used independently
    without requiring a client instance.
    """
    if config.MCP_TRANSPORT == "stdio":
        headers = {"X-API-Key": config.KOMODOR_API_KEY, "User-Agent": "komodor/mcp"}
        return KomodorClient(headers)

    request = mcp.get_context().request_context.request
    api_key = request.headers.get("Authorization") or request.headers.get("X-API-Key")
    if api_key and "Bearer" in api_key:
        api_key = api_key.split(" ")[1]
    if not api_key:
        raise ValueError("API key required in headers")

    headers = {"X-API-Key": api_key, "User-Agent": "komodor/mcp"}
    return KomodorClient(headers)
