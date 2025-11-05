from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    @mcp.prompt(
        name="Komodor Health Overview",
        description="Comprehensive health analysis of cluster violations and unhealthy services with actionable recommendations.",
        title="KomodorHealthOverview",
    )
    async def komodor_health_overview(
        cluster_name: str, namespace: str | None = None
    ) -> str:
        return f"""
        You are a Kubernetes health analysis expert that provides comprehensive insights into cluster health issues and service status.

        **Analysis Scope:**
        - Cluster: {cluster_name}
        - Namespace: {namespace if namespace else "All namespaces"}
        - Time Range: Last 24 hours
        - Data Limit: 100 items

        **Step 1: Health Risk Analysis**
        Call get_health_risks with these parameters:
        - cluster_name="{cluster_name}"
        - namespaces={f'["{namespace}"]' if namespace else None}
        - status=["open", "confirmed"]
        - check_category=["workload", "infrastructure"]
        - page_size=100
        - offset=0

        komodorUid format is Kind|Cluster|Namespace|Name

        **Step 2: Service Health Analysis**
        Call get_services_by with these parameters:
        - cluster="{cluster_name}"
        - namespaces={f'["{namespace}"]' if namespace else None}
        - status="unhealthy"

        **Analysis Requirements:**
        1. **Health Risks Summary:**
           - Categorize by severity (Critical, High, Medium, Low)
           - Group by violation type and affected resources
           - Identify patterns and recurring issues
           - Highlight the most impactful violations

        2. **Unhealthy Services Summary:**
           - List services with health issues
           - Identify common failure patterns
           - Note resource constraints or configuration problems

        3. **Actionable Recommendations:**
           - Prioritize fixes by impact and effort
           - Suggest immediate actions for critical issues
           - Recommend RCA (Root Cause Analysis) for complex problems

        **Output Format:**
        - Executive summary with key metrics
        - Detailed findings with specific resource names
        - Prioritized action plan
        - Next steps for deeper investigation

        Ensure the report is concise, actionable, and focuses on business impact.
    """

    @mcp.prompt(
        name="Komodor Root Cause Analysis",
        description="Perform deep-dive RCA on specific health issues using Klaudia AI analysis.",
        title="KomodorRCA",
    )
    async def komodor_rca_analysis(
        cluster_name: str,
        service_name: str,
        namespace: str,
        issue_description: str | None = None,
    ) -> str:
        return f"""
        You are a Kubernetes troubleshooting expert specializing in root cause analysis using AI-powered insights.

        **RCA Request Details:**
        - Cluster: {cluster_name}
        - Service: {service_name}
        - Namespace: {namespace}
        - Issue: {issue_description if issue_description else "No issue description provided"}

        **Analysis Process:**

        **Step 1: Service Context**
        Call get_service_yaml to understand the service configuration:
        - cluster="{cluster_name}"
        - service_name="{service_name}"
        - namespace="{namespace}"

        **Step 2: Health Risk Investigation**
        Call get_health_risks to find related violations:
        - cluster_name="{cluster_name}"
        - namespaces=["{namespace}"]
        - status=["open", "confirmed"]
        - page_size=50

        **Step 3: AI-Powered RCA**
        Call trigger_klaudia_rca to initiate AI analysis:
        - cluster_name="{cluster_name}"
        - service_name="{service_name}"
        - namespace="{namespace}"
        - issue_description="{issue_description if issue_description else "No issue description provided"}"

        **Step 4: Retrieve RCA Results**
        Call get_klaudia_rca_results to get AI analysis:
        - cluster_name="{cluster_name}"
        - service_name="{service_name}"
        - namespace="{namespace}"

        **Analysis Framework:**
        1. **Problem Definition:**
           - Clear statement of the issue
           - Affected components and impact
           - Timeline of events

        2. **Technical Analysis:**
           - Service configuration review
           - Resource constraints analysis
           - Dependency mapping
           - Log pattern analysis

        3. **AI Insights:**
           - Klaudia's root cause findings
           - Confidence levels and evidence
           - Related issues and patterns

        4. **Resolution Strategy:**
           - Immediate mitigation steps
           - Long-term fixes
           - Prevention measures
           - Monitoring improvements

        **Output Requirements:**
        - Executive summary of findings
        - Technical root cause explanation
        - Step-by-step resolution plan
        - Confidence assessment of the analysis, based on the evidence and the analysis.

        Focus on providing actionable insights that help resolve the issue and prevent recurrence.
    """
