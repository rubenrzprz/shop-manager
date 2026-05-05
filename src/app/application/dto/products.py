from dataclasses import dataclass, field
from decimal import Decimal
from typing import Final


class _Unset:
    pass


UNSET: Final = _Unset()


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
    category_ids: list[int] = field(default_factory=list)
    variants: list[CreateProductVariantInput] = field(default_factory=list)


@dataclass(frozen=True)
class UpdateProductVariantInput:
    variant_id: int
    size: str | None | _Unset = UNSET
    color: str | None | _Unset = UNSET
    variant_name: str | None | _Unset = UNSET
    description: str | None | _Unset = UNSET
    price_override: Decimal | None | _Unset = UNSET
    stock_current: int | None | _Unset = UNSET
    stock_minimum: int | None | _Unset = UNSET


@dataclass(frozen=True)
class UpdateProductInput:
    name: str | _Unset = UNSET
    supplier_id: int | None | _Unset = UNSET
    description: str | None | _Unset = UNSET
    base_price: Decimal | None | _Unset = UNSET
    track_stock: bool | _Unset = UNSET
    category_ids: list[int] | _Unset = UNSET
    default_variant: UpdateProductVariantInput | None = None


@dataclass(frozen=True)
class ProductCategorySummary:
    id: int
    name: str
    is_active: bool


@dataclass(frozen=True)
class ProductVariantEditItem:
    id: int
    sku: str
    size: str | None
    color: str | None
    variant_name: str | None
    description: str | None
    price_override: Decimal | None
    stock_current: int | None
    stock_minimum: int | None
    is_active: bool


@dataclass(frozen=True)
class ProductEditItem:
    id: int
    supplier_id: int | None
    supplier_name: str | None
    name: str
    description: str | None
    base_price: Decimal | None
    track_stock: bool
    is_active: bool
    categories: list[ProductCategorySummary]
    default_variant: ProductVariantEditItem
    variants: list[ProductVariantEditItem]


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
    stock_current: int | None
    stock_minimum: int | None
    is_active: bool


@dataclass(frozen=True)
class ProductListFilters:
    search_text: str | None = None
    category_id: int | None = None
    uncategorized_only: bool = False


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
    categories: list[ProductCategorySummary]
    variants: list[ProductVariantListItem]


@dataclass(frozen=True)
class ProductVariantPickerItem:
    id: int
    product_id: int
    product_name: str
    sku: str
    size: str | None
    color: str | None
    variant_name: str | None
    price: Decimal | None
    product_is_active: bool
    variant_is_active: bool
    category_names: list[str] = field(default_factory=list)
