from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.dto.customers import (
    CreateCustomerInput,
    CustomerEditItem,
    CustomerListItem,
    UpdateCustomerInput,
)
from app.infrastructure.db.models.customers import Customer


class CreateCustomerService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, data: CreateCustomerInput) -> Customer:
        self._validate_customer_input(data)

        customer = Customer(
            customer_type=data.customer_type,
            name=data.name.strip(),
            company_name=data.company_name,
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

        self._session.add(customer)
        self._session.flush()

        return customer

    @staticmethod
    def _validate_customer_input(data: CreateCustomerInput | UpdateCustomerInput) -> None:
        if not data.name or not data.name.strip():
            raise ValueError("Customer name is required.")


class UpdateCustomerService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, customer_id: int, data: UpdateCustomerInput) -> Customer:
        CreateCustomerService._validate_customer_input(data)

        customer = self._session.get(Customer, customer_id)

        if customer is None:
            raise ValueError("Customer not found.")

        customer.customer_type = data.customer_type
        customer.name = data.name.strip()
        customer.company_name = data.company_name
        customer.tax_id = data.tax_id
        customer.phone = data.phone
        customer.email = data.email
        customer.address_line_1 = data.address_line_1
        customer.address_line_2 = data.address_line_2
        customer.postal_code = data.postal_code
        customer.city = data.city
        customer.country = data.country
        customer.notes = data.notes
        customer.is_active = data.is_active

        self._session.flush()

        return customer


class ListCustomersService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self) -> list[CustomerListItem]:
        statement = select(Customer).order_by(Customer.name, Customer.id)
        customers = self._session.scalars(statement).all()

        return [
            CustomerListItem(
                id=customer.id,
                customer_type=customer.customer_type,
                name=customer.name,
                company_name=customer.company_name,
                tax_id=customer.tax_id,
                phone=customer.phone,
                email=customer.email,
                city=customer.city,
                country=customer.country,
                is_active=customer.is_active,
            )
            for customer in customers
        ]


class GetCustomerForEditService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, customer_id: int) -> CustomerEditItem:
        customer = self._session.get(Customer, customer_id)

        if customer is None:
            raise ValueError("Customer not found.")

        return CustomerEditItem(
            id=customer.id,
            customer_type=customer.customer_type,
            name=customer.name,
            company_name=customer.company_name,
            tax_id=customer.tax_id,
            phone=customer.phone,
            email=customer.email,
            address_line_1=customer.address_line_1,
            address_line_2=customer.address_line_2,
            postal_code=customer.postal_code,
            city=customer.city,
            country=customer.country,
            notes=customer.notes,
            is_active=customer.is_active,
        )
