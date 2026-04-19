from dataclasses import dataclass


@dataclass(frozen=True)
class ApplicationSettingsItem:
    strict_order_workflow_enabled: bool = False
