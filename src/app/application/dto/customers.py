from dataclasses import dataclass

from app.domain.enums import CustomerType


@dataclass(frozen=True)
class CreateCustomerInput:
    customer_type: CustomerType
    name: str
    company_name: str | None = None
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
class UpdateCustomerInput:
    customer_type: CustomerType
    name: str
    company_name: str | None = None
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
class CustomerListItem:
    id: int
    customer_type: CustomerType
    name: str
    company_name: str | None
    tax_id: str | None
    phone: str | None
    email: str | None
    city: str | None
    country: str | None
    is_active: bool


@dataclass(frozen=True)
class CustomerEditItem:
    id: int
    customer_type: CustomerType
    name: str
    company_name: str | None
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
class CustomerPickerItem:
    id: int
    customer_type: CustomerType
    name: str
    company_name: str | None
    tax_id: str | None
    phone: str | None
    email: str | None
    is_active: bool
