import asyncio
from typing import Any, Literal

from mcp.server.fastmcp import Context, FastMCP
from openapi_client.models.check_category import CheckCategory
from openapi_client.models.clusters_data import ClustersData
from openapi_client.models.get_all_health_risks_response import (
    GetAllHealthRisksResponse,
)
from openapi_client.models.get_violation_response import GetViolationResponse
from openapi_client.models.impact_group_type import ImpactGroupType
from openapi_client.models.klaudia_rca_results_response import KlaudiaRcaResultsResponse
from openapi_client.models.search_services_response import SearchServicesResponse
from openapi_client.models.service_kind import ServiceKind
from openapi_client.models.violation_status import ViolationStatus

from .api_client import create_authenticated_client


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_clusters() -> ClustersData:
        """Get list of all clusters in the Komodor workspace.

        Returns cluster data containing cluster metadata.
        Each cluster object includes cluster name, status, and other relevant information.
        if you want to match komodor cluster name with local context name:
            - run `helm get values komodor-agent` if helm exists, `helm get values komodor-agent | yq '.clusterName'` if yq also exists.
            - otherwise you can use kubectl `kubectl get configmap komodor-agent-config -n default -o jsonpath='{.data.komodor-k8s-watcher\\.yaml}' | yq '.clusterName'`
        """
        try:
            async with create_authenticated_client(mcp) as auth_client:
                response = await auth_client.get_clusters()
                if response and hasattr(response, "data"):
                    return response.data
                else:
                    raise Exception("No cluster data available")
        except Exception as e:
            raise Exception(f"Failed to get clusters: {str(e)}") from e

    @mcp.tool()
    async def get_services_by(
        cluster: str | None = None,
        namespaces: list[str] | None = None,
        service_kind: list[ServiceKind] | None = None,
        status: Literal["healthy", "unhealthy"] = "unhealthy",
    ) -> SearchServicesResponse:
        """Search and retrieve Kubernetes services based on filtering criteria.

        This tool allows you to search for services across clusters and namespaces with pagination support.
        You can filter by specific cluster, namespace(s), or get all services if no filters are provided.

        Example:
            get_services_by(cluster="prod-cluster", namespaces=["default", "monitoring"])
            Returns: Services data object with services array
        """
        try:
            async with create_authenticated_client(mcp) as auth_client:
                response = await auth_client.search_services(
                    cluster=cluster,
                    namespaces=namespaces,
                    service_kind=service_kind,
                    status=status,
                )
                return response
        except Exception as e:
            raise Exception(f"Failed to get services: {str(e)}") from e

    @mcp.tool()
    async def get_service_yaml(
        cluster: str, namespace: str, kind: ServiceKind, name: str
    ) -> object:
        """Retrieve the complete YAML configuration for a specific Kubernetes resource.

        This tool fetches the full YAML manifest of a Kubernetes resource, including all
        specifications, metadata, and configuration details. Useful for understanding
        resource configuration, troubleshooting, or comparing configurations.

        Example:
            get_service_yaml(cluster="prod-cluster", namespace="default", kind="Deployment", name="data-processor")
            Returns: Service YAML data object
        """
        try:
            async with create_authenticated_client(mcp) as auth_client:
                response = await auth_client.get_service_yaml(
                    cluster, namespace, kind, name
                )
                return response
        except Exception as e:
            raise Exception(f"Failed to get service YAML: {str(e)}") from e

    @mcp.tool()
    async def get_health_risks(
        cluster_name: list[str] | None = None,
        namespace: list[str] | None = None,
        status: list[ViolationStatus] = [
            ViolationStatus.OPEN,
            ViolationStatus.CONFIRMED,
        ],
        check_category: list[CheckCategory] = [
            CheckCategory.WORKLOAD,
            CheckCategory.INFRASTRUCTURE,
        ],
        page_size: int = 100,
        offset: int = 0,
    ) -> GetAllHealthRisksResponse:
        """Retrieve health risks and violations across your Kubernetes infrastructure.

        This tool identifies potential issues, misconfigurations, and health problems in your
        clusters. It provides comprehensive filtering options to focus on specific areas of concern.
        Use at least namespace or cluster_name to get relevant results.
        check_category is default for workloads, if you looking for infrastructure issues, you can set it to infrastructure.
        status is default for open and confirmed, avoid using other statuses, unless you asked specifically for other statuses.

        Example:
            get_health_risks(status=["open"], cluster_name=["prod-cluster"])
            Returns: Health risks data object with violations array
        """
        try:
            async with create_authenticated_client(mcp) as auth_client:
                response = await auth_client.get_health_risks(
                    page_size=page_size,
                    offset=offset,
                    impact_group_type=[ImpactGroupType.REALTIME],
                    status=status,
                    cluster_name=cluster_name,
                    namespace=namespace,
                    check_category=check_category,
                )

                # Remove supportingData from each violation
                if response and hasattr(response, "violations") and response.violations:
                    for violation in response.violations:
                        if hasattr(violation, "supporting_data"):
                            violation.supporting_data = None

                return response
        except Exception as e:
            raise Exception(f"Failed to get health risks: {str(e)}") from e

    @mcp.tool()
    async def get_health_risk_data(risk_id: str) -> GetViolationResponse:
        """Get comprehensive details for a specific health risk or violation.

        This tool provides in-depth information about a particular health risk, including
        detailed analysis, root cause information, remediation suggestions, and historical
        context. Use this after identifying risks with get_health_risks to get full details.

        Example:
            get_health_risk_data(risk_id="7e3eeda1-b70c-44be-826d-87e68b0d3e2c")
            Returns detailed analysis of the specific health risk
        """
        try:
            async with create_authenticated_client(mcp) as auth_client:
                response = await auth_client.get_health_risk_data(risk_id)
                return response
        except Exception as e:
            raise Exception(f"Failed to get health risk data: {str(e)}") from e

    @mcp.tool()
    async def trigger_klaudia_rca(
        cluster: str,
        namespace: str,
        resource_kind: str,
        resource_name: str,
        wait: bool | None = True,
        ctx: Context = None,
    ) -> KlaudiaRcaResultsResponse:
        """Trigger an automated Root Cause Analysis (RCA) investigation using Klaudia AI.

        Klaudia is Komodor's AI-powered RCA engine that analyzes incidents and provides
        intelligent insights into what went wrong. This tool initiates a comprehensive
        investigation of a specific resource and can wait for completion.

        Example:
            trigger_klaudia_rca(cluster="prod", namespace="default", resource_kind="Deployment", resource_name="api-server")
            Returns comprehensive RCA analysis of the api-server deployment issues
        """
        try:
            if ctx:
                await ctx.info(
                    f"Starting Klaudia RCA investigation for {resource_kind}/{resource_name} in {namespace}@{cluster}"
                )

            async with create_authenticated_client(mcp) as auth_client:
                response = await auth_client.trigger_klaudia_rca(
                    cluster=cluster,
                    namespace=namespace,
                    resource_kind=resource_kind,
                    resource_name=resource_name,
                )
                session_id = response.session_id
                if wait and ctx:
                    await ctx.info(
                        f"RCA investigation started for session: {session_id}, waiting for completion..."
                    )
                    response = await auth_client.get_klaudia_rca_results(session_id)
                    check_count = 0
                    while not response.is_complete:
                        check_count += 1
                        progress = round(
                            min(0.9, check_count * 0.1), 1
                        )  # Cap at 90% until complete
                        await ctx.report_progress(
                            progress=progress,
                            total=1.0,
                            message=f"Checking RCA status for session: {session_id} (attempt {check_count})",
                        )
                        await asyncio.sleep(5)
                        response = await auth_client.get_klaudia_rca_results(session_id)

                    await ctx.report_progress(
                        progress=1.0, total=1.0, message="RCA investigation completed!"
                    )
                    await ctx.info(
                        f"RCA investigation completed successfully for session: {session_id}"
                    )
                elif wait:
                    while not response.is_complete:
                        await asyncio.sleep(5)
                        response = await auth_client.get_klaudia_rca_results(session_id)

                return response
        except Exception as e:
            if ctx:
                await ctx.error(f"RCA investigation failed: {str(e)}")
            raise Exception(f"RCA investigation failed: {str(e)}") from e

    @mcp.tool()
    async def get_klaudia_rca_results(
        session_id: str, wait: bool = True, ctx: Context[Any, Any, Any] | None = None
    ) -> KlaudiaRcaResultsResponse:
        """Retrieve results from a previously initiated Klaudia RCA investigation.

        Use this tool to check the status and get results from an ongoing or completed
        RCA investigation. The session_id is obtained from trigger_klaudia_rca.

        Example:
            get_klaudia_rca_results(session_id="rca-session-123", wait=True)
            Returns the complete RCA analysis results
        """
        try:
            if ctx:
                await ctx.info(
                    f"Fetching Klaudia RCA results for session: {session_id}"
                )

            async with create_authenticated_client(mcp) as auth_client:
                response = await auth_client.get_klaudia_rca_results(session_id)
                if response.is_complete:
                    wait = False

                if wait and ctx:
                    await ctx.info(
                        f"Checking RCA completion status for session: {session_id}"
                    )
                    check_count = 0
                    while not response.is_complete:
                        check_count += 1
                        progress = round(
                            min(0.9, check_count * 0.1), 1
                        )  # Cap at 90% until complete
                        await ctx.report_progress(
                            progress=progress,
                            total=1.0,
                            message=f"Checking RCA status... (attempt {check_count})",
                        )
                        await ctx.info(
                            f"Checking RCA status for session: {session_id} (attempt {check_count})"
                        )
                        await asyncio.sleep(5)
                        response = await auth_client.get_klaudia_rca_results(session_id)

                    await ctx.report_progress(
                        progress=1.0, total=1.0, message="RCA results ready!"
                    )
                    await ctx.info("RCA results retrieved successfully")
                elif wait:
                    while not response.is_complete:
                        await asyncio.sleep(5)
                        response = await auth_client.get_klaudia_rca_results(session_id)

                return response
        except Exception as e:
            if ctx:
                await ctx.error(f"Failed to get RCA results: {str(e)}")
            raise Exception(f"Failed to get RCA results: {str(e)}") from e
