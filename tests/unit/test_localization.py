from app.domain.enums import OrderStatus
from app.ui.localization import order_status_label, set_language, t


def teardown_function():
    set_language("en")


def test_translation_uses_english_as_default():
    set_language("en")

    assert t("Orders") == "Orders"


def test_translation_returns_spanish_text_when_language_is_spanish():
    set_language("es")

    assert t("Orders") == "Pedidos"
    assert order_status_label(OrderStatus.IN_PROGRESS) == "En curso"


def test_translation_falls_back_to_key_for_missing_text():
    set_language("es")

    assert t("Not translated yet") == "Not translated yet"
