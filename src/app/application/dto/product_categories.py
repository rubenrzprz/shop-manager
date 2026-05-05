from dataclasses import dataclass


@dataclass(frozen=True)
class CreateProductCategoryInput:
    name: str
    description: str | None = None
    is_active: bool = True


@dataclass(frozen=True)
class UpdateProductCategoryInput:
    name: str
    description: str | None = None
    is_active: bool = True


@dataclass(frozen=True)
class ProductCategoryListItem:
    id: int
    name: str
    description: str | None
    is_active: bool


@dataclass(frozen=True)
class ProductCategoryEditItem:
    id: int
    name: str
    description: str | None
    is_active: bool


@dataclass(frozen=True)
class ProductCategoryOption:
    id: int
    name: str
    description: str | None
    is_active: bool
