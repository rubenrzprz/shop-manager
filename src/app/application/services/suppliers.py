from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.dto.suppliers import (
    CreateSupplierInput,
    SupplierEditItem,
    SupplierListItem,
    SupplierPickerItem,
    UpdateSupplierInput,
)
from app.infrastructure.db.models.suppliers import Supplier


class CreateSupplierService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, data: CreateSupplierInput) -> Supplier:
        self._validate_supplier_input(data)

        supplier = Supplier(
            name=data.name.strip(),
            tax_id=data.tax_id,
            phone=data.phone,
            email=data.email,
            address_line_1=data.address_line_1,
            address_line_2=data.address_line_2,
            postal_code=data.postal_code,
            city=data.city,
            country=data.country,
            notes=data.notes,
            is_active=data.is_active,
        )

        self._session.add(supplier)
        self._session.flush()

        return supplier

    @staticmethod
    def _validate_supplier_input(data: CreateSupplierInput | UpdateSupplierInput) -> None:
        if not data.name or not data.name.strip():
            raise ValueError("Supplier name is required.")


class UpdateSupplierService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, supplier_id: int, data: UpdateSupplierInput) -> Supplier:
        CreateSupplierService._validate_supplier_input(data)

        supplier = self._session.get(Supplier, supplier_id)

        if supplier is None:
            raise ValueError("Supplier not found.")

        supplier.name = data.name.strip()
        supplier.tax_id = data.tax_id
        supplier.phone = data.phone
        supplier.email = data.email
        supplier.address_line_1 = data.address_line_1
        supplier.address_line_2 = data.address_line_2
        supplier.postal_code = data.postal_code
        supplier.city = data.city
        supplier.country = data.country
        supplier.notes = data.notes
        supplier.is_active = data.is_active

        self._session.flush()

        return supplier


class ListSuppliersService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self) -> list[SupplierListItem]:
        statement = select(Supplier).order_by(Supplier.name, Supplier.id)
        suppliers = self._session.scalars(statement).all()

        return [
            SupplierListItem(
                id=supplier.id,
                name=supplier.name,
                tax_id=supplier.tax_id,
                phone=supplier.phone,
                email=supplier.email,
                city=supplier.city,
                country=supplier.country,
                is_active=supplier.is_active,
            )
            for supplier in suppliers
        ]


class GetSupplierForEditService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, supplier_id: int) -> SupplierEditItem:
        supplier = self._session.get(Supplier, supplier_id)

        if supplier is None:
            raise ValueError("Supplier not found.")

        return SupplierEditItem(
            id=supplier.id,
            name=supplier.name,
            tax_id=supplier.tax_id,
            phone=supplier.phone,
            email=supplier.email,
            address_line_1=supplier.address_line_1,
            address_line_2=supplier.address_line_2,
            postal_code=supplier.postal_code,
            city=supplier.city,
            country=supplier.country,
            notes=supplier.notes,
            is_active=supplier.is_active,
        )


class ListSupplierPickerOptionsService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self) -> list[SupplierPickerItem]:
        statement = select(Supplier).order_by(Supplier.name, Supplier.id)
        suppliers = self._session.scalars(statement).all()

        return [
            SupplierPickerItem(
                id=supplier.id,
                name=supplier.name,
                tax_id=supplier.tax_id,
                phone=supplier.phone,
                email=supplier.email,
                is_active=supplier.is_active,
            )
            for supplier in suppliers
        ]
