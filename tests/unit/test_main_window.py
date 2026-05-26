from app.ui.windows.main_window import MainWindow


def test_language_change_retranslates_and_reloads_dashboard():
    calls = []
    window = MainWindow.__new__(MainWindow)

    class FakeDashboardPage:
        def reload_dashboard(self):
            calls.append("reload_dashboard")

    window._dashboard_page = FakeDashboardPage()
    window.retranslate_ui = lambda: calls.append("retranslate_ui")

    MainWindow._handle_language_changed(window, "es")

    assert calls == ["retranslate_ui", "reload_dashboard"]
