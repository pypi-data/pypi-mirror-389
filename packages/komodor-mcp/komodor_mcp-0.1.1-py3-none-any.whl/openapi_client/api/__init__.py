# flake8: noqa

if __import__("typing").TYPE_CHECKING:
    # import apis into api package
    from openapi_client.api.api_key_api import ApiKeyApi
    from openapi_client.api.audit_logs_api import AuditLogsApi
    from openapi_client.api.clusters_api import ClustersApi
    from openapi_client.api.custom_events_api import CustomEventsApi
    from openapi_client.api.events_api import EventsApi
    from openapi_client.api.health_risks_api import HealthRisksApi
    from openapi_client.api.issues_api import IssuesApi
    from openapi_client.api.jobs_api import JobsApi
    from openapi_client.api.klaudia_api import KlaudiaApi
    from openapi_client.api.komodor_cost_api import KomodorCostApi
    from openapi_client.api.kubeconfig_api import KubeconfigApi
    from openapi_client.api.monitors_api import MonitorsApi
    from openapi_client.api.policies_api import PoliciesApi
    from openapi_client.api.rbac_api import RbacApi
    from openapi_client.api.real_time_monitors_api import RealTimeMonitorsApi
    from openapi_client.api.roles_api import RolesApi
    from openapi_client.api.services_api import ServicesApi
    from openapi_client.api.users_api import UsersApi
    from openapi_client.api.integrations_api import IntegrationsApi

else:
    from lazy_imports import LazyModule, as_package, load

    load(
        LazyModule(
            *as_package(__file__),
            """# import apis into api package
from openapi_client.api.api_key_api import ApiKeyApi
from openapi_client.api.audit_logs_api import AuditLogsApi
from openapi_client.api.clusters_api import ClustersApi
from openapi_client.api.custom_events_api import CustomEventsApi
from openapi_client.api.events_api import EventsApi
from openapi_client.api.health_risks_api import HealthRisksApi
from openapi_client.api.issues_api import IssuesApi
from openapi_client.api.jobs_api import JobsApi
from openapi_client.api.klaudia_api import KlaudiaApi
from openapi_client.api.komodor_cost_api import KomodorCostApi
from openapi_client.api.kubeconfig_api import KubeconfigApi
from openapi_client.api.monitors_api import MonitorsApi
from openapi_client.api.policies_api import PoliciesApi
from openapi_client.api.rbac_api import RbacApi
from openapi_client.api.real_time_monitors_api import RealTimeMonitorsApi
from openapi_client.api.roles_api import RolesApi
from openapi_client.api.services_api import ServicesApi
from openapi_client.api.users_api import UsersApi
from openapi_client.api.integrations_api import IntegrationsApi

""",
            name=__name__,
            doc=__doc__,
        )
    )
