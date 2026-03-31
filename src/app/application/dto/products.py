from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class CreateProductVariantInput:
    sku: str | None = None
    size: str | None = None
    color: str | None = None
    variant_name: str | None = None
    description: str | None = None
    price_override: Decimal | None = None
    stock_current: int | None = None
    stock_minimum: int | None = None
    is_active: bool = True

@dataclass(frozen=True)
class CreateProductInput:
    name: str
    supplier_id: int | None = None
    description: str | None = None
    base_price: Decimal | None = None
    track_stock: bool = False
    is_active: bool = True
    variants: list[CreateProductVariantInput] = field(default_factory=list)