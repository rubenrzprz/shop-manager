from sqlalchemy.orm import Session

from app.application.dto.settings import ApplicationSettingsItem
from app.infrastructure.db.models.settings import ApplicationSetting

STRICT_ORDER_WORKFLOW_ENABLED_KEY = "strict_order_workflow_enabled"
APP_LANGUAGE_KEY = "app_language"
SUPPORTED_APP_LANGUAGES = {"en", "es"}


class ApplicationSettingsService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_settings(self) -> ApplicationSettingsItem:
        return ApplicationSettingsItem(
            strict_order_workflow_enabled=self.strict_order_workflow_enabled(),
            app_language=self.app_language(),
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
