from dataclasses import dataclass


@dataclass(frozen=True)
class CreateSupplierInput:
    name: str
    tax_id: str | None = None
    phone: str | None = None
    email: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country: str | None = None
    notes: str | None = None
    is_active: bool = True


@dataclass(frozen=True)
class UpdateSupplierInput:
    name: str
    tax_id: str | None = None
    phone: str | None = None
    email: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country: str | None = None
    notes: str | None = None
    is_active: bool = True


@dataclass(frozen=True)
class SupplierListItem:
    id: int
    name: str
    tax_id: str | None
    phone: str | None
    email: str | None
    city: str | None
    country: str | None
    is_active: bool


@dataclass(frozen=True)
class SupplierEditItem:
    id: int
    name: str
    tax_id: str | None
    phone: str | None
    email: str | None
    address_line_1: str | None
    address_line_2: str | None
    postal_code: str | None
    city: str | None
    country: str | None
    notes: str | None
    is_active: bool


@dataclass(frozen=True)
class SupplierPickerItem:
    id: int
    name: str
    tax_id: str | None
    phone: str | None
    email: str | None
    is_active: bool
