from app.application.services.products import CreateProductService


def test_generate_prefix_falls_back_for_non_ascii_only_names():
    service = CreateProductService(session=None)  # type: ignore[arg-type]

    assert service._generate_prefix("你好世界") == "PRD"
    assert service._generate_sku("你好世界", 12, 1) == "PRD-0012-01"
