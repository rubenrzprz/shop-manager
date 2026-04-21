import json

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.application.dto.settings import ApplicationSettingsItem
from app.domain.enums import OrderStatus
from app.infrastructure.db.models.orders import Order
from app.infrastructure.db.models.settings import ApplicationSetting

STRICT_ORDER_WORKFLOW_ENABLED_KEY = "strict_order_workflow_enabled"
APP_LANGUAGE_KEY = "app_language"
ENABLED_ORDER_STATUSES_KEY = "enabled_order_statuses"
SUPPORTED_APP_LANGUAGES = {"en", "es"}
ORDER_STATUS_WORKFLOW = (
    OrderStatus.DRAFT,
    OrderStatus.CONFIRMED,
    OrderStatus.IN_PROGRESS,
    OrderStatus.READY,
    OrderStatus.COMPLETED,
    OrderStatus.CANCELLED,
)
REQUIRED_ORDER_STATUSES = {
    OrderStatus.DRAFT,
    OrderStatus.COMPLETED,
    OrderStatus.CANCELLED,
}
OPTIONAL_ORDER_STATUSES = tuple(
    status for status in ORDER_STATUS_WORKFLOW if status not in REQUIRED_ORDER_STATUSES
)


class ApplicationSettingsService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_settings(self) -> ApplicationSettingsItem:
        return ApplicationSettingsItem(
            strict_order_workflow_enabled=self.strict_order_workflow_enabled(),
            app_language=self.app_language(),
            enabled_order_statuses=self.enabled_order_statuses(),
        )

    def strict_order_workflow_enabled(self) -> bool:
        return self._get_bool(STRICT_ORDER_WORKFLOW_ENABLED_KEY, default=False)

    def app_language(self) -> str:
        return self._get_string(APP_LANGUAGE_KEY, default="en")

    def set_app_language(self, value: str) -> None:
        normalized_value = value.strip().lower()
        if normalized_value not in SUPPORTED_APP_LANGUAGES:
            raise ValueError("Application language must be one of: en, es.")

        self._set_string(
            APP_LANGUAGE_KEY,
            normalized_value,
            "Language used for user-facing application text.",
        )

    def enabled_order_statuses(self) -> tuple[OrderStatus, ...]:
        raw_values = self._get_json_list(
            ENABLED_ORDER_STATUSES_KEY,
            default=[status.value for status in ORDER_STATUS_WORKFLOW],
        )
        statuses = self._normalize_order_statuses(raw_values)
        self._validate_enabled_order_statuses(statuses)
        return statuses

    def set_enabled_order_statuses(
        self, values: list[OrderStatus] | tuple[OrderStatus, ...]
    ) -> None:
        statuses = self._normalize_order_statuses(
            [value.value if isinstance(value, OrderStatus) else value for value in values]
        )
        self._validate_enabled_order_statuses(statuses)
        self._convert_disabled_status_orders_to_draft(statuses)
        self._set_json_list(
            ENABLED_ORDER_STATUSES_KEY,
            [status.value for status in statuses],
            "Order statuses enabled in the forward/revert workflow.",
        )

    def disabled_order_status_conversion_counts(
        self, values: list[OrderStatus] | tuple[OrderStatus, ...]
    ) -> dict[OrderStatus, int]:
        statuses = self._normalize_order_statuses(
            [value.value if isinstance(value, OrderStatus) else value for value in values]
        )
        self._validate_enabled_order_statuses(statuses)
        disabled_statuses = self._disabled_optional_statuses(statuses)
        if not disabled_statuses:
            return {}

        rows = self._session.execute(
            select(Order.status, func.count(Order.id))
            .where(Order.status.in_(disabled_statuses))
            .group_by(Order.status)
        ).all()
        counts_by_status = {status: count for status, count in rows}

        return {
            status: counts_by_status[status]
            for status in ORDER_STATUS_WORKFLOW
            if status in counts_by_status
        }

    def set_strict_order_workflow_enabled(self, value: bool) -> None:
        self._set_bool(
            STRICT_ORDER_WORKFLOW_ENABLED_KEY,
            value,
            "Use status-specific order editing rules instead of simple active-order editing.",
        )

    def _get_bool(self, key: str, *, default: bool) -> bool:
        setting = self._session.get(ApplicationSetting, key)
        if setting is None:
            return default

        normalized_value = setting.value.strip().lower()
        if normalized_value == "true":
            return True
        if normalized_value == "false":
            return False

        raise ValueError(f"Application setting {key} must be a boolean value.")

    def _get_string(self, key: str, *, default: str) -> str:
        setting = self._session.get(ApplicationSetting, key)
        if setting is None:
            return default

        if key == APP_LANGUAGE_KEY and setting.value not in SUPPORTED_APP_LANGUAGES:
            raise ValueError("Application language must be one of: en, es.")

        return setting.value

    def _get_json_list(self, key: str, *, default: list[str]) -> list[str]:
        setting = self._session.get(ApplicationSetting, key)
        if setting is None:
            return default

        try:
            value = json.loads(setting.value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Application setting {key} must be a JSON list.") from exc

        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ValueError(f"Application setting {key} must be a JSON list.")

        return value

    def _set_bool(self, key: str, value: bool, description: str) -> None:
        setting = self._session.get(ApplicationSetting, key)
        serialized_value = "true" if value else "false"

        if setting is None:
            self._session.add(
                ApplicationSetting(
                    key=key,
                    value=serialized_value,
                    value_type="bool",
                    description=description,
                )
            )
            return

        setting.value = serialized_value
        setting.value_type = "bool"
        setting.description = description

    def _set_string(self, key: str, value: str, description: str) -> None:
        setting = self._session.get(ApplicationSetting, key)

        if setting is None:
            self._session.add(
                ApplicationSetting(
                    key=key,
                    value=value,
                    value_type="string",
                    description=description,
                )
            )
            return

        setting.value = value
        setting.value_type = "string"
        setting.description = description

    def _set_json_list(self, key: str, value: list[str], description: str) -> None:
        setting = self._session.get(ApplicationSetting, key)
        serialized_value = json.dumps(value)

        if setting is None:
            self._session.add(
                ApplicationSetting(
                    key=key,
                    value=serialized_value,
                    value_type="json",
                    description=description,
                )
            )
            return

        setting.value = serialized_value
        setting.value_type = "json"
        setting.description = description

    @staticmethod
    def _normalize_order_statuses(values: list[str]) -> tuple[OrderStatus, ...]:
        try:
            selected_statuses = {OrderStatus(value) for value in values}
        except ValueError as exc:
            raise ValueError("Enabled order statuses contain an unsupported status.") from exc

        return tuple(status for status in ORDER_STATUS_WORKFLOW if status in selected_statuses)

    @staticmethod
    def _validate_enabled_order_statuses(statuses: tuple[OrderStatus, ...]) -> None:
        missing_required_statuses = REQUIRED_ORDER_STATUSES - set(statuses)
        if missing_required_statuses:
            required_values = ", ".join(
                status.value
                for status in ORDER_STATUS_WORKFLOW
                if status in REQUIRED_ORDER_STATUSES
            )
            raise ValueError(f"Enabled order statuses must include: {required_values}.")

    @staticmethod
    def _disabled_optional_statuses(statuses: tuple[OrderStatus, ...]) -> tuple[OrderStatus, ...]:
        selected_statuses = set(statuses)
        return tuple(
            status for status in OPTIONAL_ORDER_STATUSES if status not in selected_statuses
        )

    def _convert_disabled_status_orders_to_draft(self, statuses: tuple[OrderStatus, ...]) -> None:
        disabled_statuses = self._disabled_optional_statuses(statuses)
        if not disabled_statuses:
            return

        self._session.execute(
            update(Order)
            .where(Order.status.in_(disabled_statuses))
            .values(status=OrderStatus.DRAFT)
        )
