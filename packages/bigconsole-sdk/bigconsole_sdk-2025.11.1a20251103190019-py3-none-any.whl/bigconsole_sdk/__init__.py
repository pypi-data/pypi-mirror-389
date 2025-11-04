from typing import Optional

from .activity import ActivityModule
from .addon import AddonModule
from .analytics import AnalyticsModule
from .auth import AuthModule
from .billing import BillingModule
from .client.base_client import BaseGraphQLClient, BigconsoleSDKConfig
from .config import ConfigModule
from .credit import CreditModule
from .discount import DiscountModule
from .export import ExportModule
from .graph import GraphModule
from .newsletter import NewsletterModule
from .notification import NotificationModule
from .organization import OrganizationModule
from .payment import PaymentModule
from .plan import PlanModule
from .product import ProductModule
from .project import ProjectModule
from .quota import QuotaModule
from .rbac import RbacModule
from .resources import ResourcesModule
from .store import StoreModule
from .store_sdk import StoreSdkModule
from .support import SupportModule
from .team import TeamModule
from .tenant import TenantModule
from .types.common import *
from .usage import UsageModule
from .user import UserModule
from .utils import UtilsModule
from .workspace import WorkspaceModule

__version__ = "2025.11.0"


class BigconsoleSDK:
    def __init__(self, config: BigconsoleSDKConfig) -> None:
        self.client = BaseGraphQLClient(config)

        # Initialize all modules
        self.activity = ActivityModule(self.client)
        self.analytics = AnalyticsModule(self.client)
        self.auth = AuthModule(self.client)
        self.billing = BillingModule(self.client)
        self.config = ConfigModule(self.client)
        self.credits = CreditModule(self.client)
        self.discounts = DiscountModule(self.client)
        self.export = ExportModule(self.client)
        self.graph = GraphModule(self.client)
        self.newsletter = NewsletterModule(self.client)
        self.notifications = NotificationModule(self.client)
        self.organizations = OrganizationModule(self.client)
        self.payments = PaymentModule(self.client)
        self.plans = PlanModule(self.client)
        self.products = ProductModule(self.client)
        self.projects = ProjectModule(self.client)
        self.quotas = QuotaModule(self.client)
        self.rbac = RbacModule(self.client)
        self.resources = ResourcesModule(self.client)
        self.store = StoreModule(self.client)
        self.store_sdk = StoreSdkModule(self.client)
        self.support = SupportModule(self.client)
        self.teams = TeamModule(self.client)
        self.tenants = TenantModule(self.client)
        self.usage = UsageModule(self.client)
        self.users = UserModule(self.client)
        self.utils = UtilsModule(self.client)
        self.workspaces = WorkspaceModule(self.client)
        self.addons = AddonModule(self.client)

    def set_tokens(self, access_token: str, refresh_token: str) -> None:
        self.client.set_tokens(access_token=access_token, refresh_token=refresh_token)

    def clear_tokens(self) -> None:
        self.client.clear_tokens()

    def get_tokens(self) -> Optional[dict]:
        tokens = self.client.get_tokens()
        return (
            {"access_token": tokens.access_token, "refresh_token": tokens.refresh_token}
            if tokens
            else None
        )

    def set_endpoint(self, endpoint: str) -> None:
        self.client.set_endpoint(endpoint)

    def get_endpoint(self) -> str:
        return self.client.get_endpoint()


__all__ = [
    "BigconsoleSDK",
    "BigconsoleSDKConfig",
    "BaseGraphQLClient",
    "ActivityModule",
    "AddonModule",
    "AnalyticsModule",
    "AuthModule",
    "BillingModule",
    "ConfigModule",
    "CreditModule",
    "DiscountModule",
    "ExportModule",
    "GraphModule",
    "NewsletterModule",
    "NotificationModule",
    "OrganizationModule",
    "PaymentModule",
    "PlanModule",
    "ProductModule",
    "ProjectModule",
    "QuotaModule",
    "RbacModule",
    "ResourcesModule",
    "StoreModule",
    "StoreSdkModule",
    "SupportModule",
    "TeamModule",
    "TenantModule",
    "UsageModule",
    "UserModule",
    "UtilsModule",
    "WorkspaceModule",
]
