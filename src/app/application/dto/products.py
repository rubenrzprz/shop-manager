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

@dataclass(frozen=True)
class UpdateProductVariantInput:
    variant_id: int
    size: str | None = None
    color: str | None = None
    variant_name: str | None = None
    description: str | None = None
    price_override: Decimal | None = None

@dataclass(frozen=True)
class UpdateProductInput:
    name: str
    supplier_id: int | None = None
    description: str | None = None
    base_price: Decimal | None = None
    track_stock: bool = False
    default_variant: UpdateProductVariantInput | None = None

@dataclass(frozen=True)
class ProductVariantEditItem:
    id: int
    sku: str
    size: str | None
    color: str | None
    variant_name: str | None
    description: str | None
    price_override: Decimal | None
    is_active: bool

@dataclass(frozen=True)
class ProductEditItem:
    id: int
    supplier_id: int | None
    name: str
    description: str | None
    base_price: Decimal | None
    track_stock: bool
    is_active: bool
    default_variant: ProductVariantEditItem

@dataclass(frozen=True)
class SupplierOption:
    id: int
    name: str

@dataclass(frozen=True)
class ProductVariantListItem:
    id: int
    sku: str
    size: str | None
    color: str | None
    variant_name: str | None
    description: str | None
    price_override: Decimal | None
    is_active: bool

@dataclass(frozen=True)
class ProductListItem:
    id: int
    supplier_id: int | None
    supplier_name: str | None
    name: str
    description: str | None
    base_price: Decimal | None
    track_stock: bool
    is_active: bool
    variants: list[ProductVariantListItem]
