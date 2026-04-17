import pytest

from app.application.dto.customers import CreateCustomerInput, UpdateCustomerInput
from app.application.services.customers import (
    CreateCustomerService,
    GetCustomerForEditService,
    ListCustomerPickerOptionsService,
    ListCustomersService,
    UpdateCustomerService,
)
from app.domain.enums import CustomerType


def test_create_customer_service_creates_customer(db_session):
    customer = CreateCustomerService(db_session).execute(
        CreateCustomerInput(
            customer_type=CustomerType.INDIVIDUAL,
            name="María Rodríguez",
            tax_id="12345678Z",
            phone="+34 600000000",
            email="maria@example.com",
            address_line_1="Calle Mayor 1",
            postal_code="38001",
            city="Santa Cruz de Tenerife",
            country="Spain",
            notes="Frequent customer",
        )
    )

    assert customer.id is not None
    assert customer.customer_type == CustomerType.INDIVIDUAL
    assert customer.name == "María Rodríguez"
    assert customer.tax_id == "12345678Z"
    assert customer.is_active is True


def test_create_customer_service_creates_company_customer(db_session):
    customer = CreateCustomerService(db_session).execute(
        CreateCustomerInput(
            customer_type=CustomerType.COMPANY,
            name="Eventos Atlántico",
            company_name="Eventos Atlántico SL",
            tax_id="B12345678",
        )
    )

    assert customer.customer_type == CustomerType.COMPANY
    assert customer.name == "Eventos Atlántico"
    assert customer.company_name == "Eventos Atlántico SL"


def test_list_customers_service_returns_customers_ordered_by_name(db_session):
    create_service = CreateCustomerService(db_session)
    create_service.execute(CreateCustomerInput(customer_type=CustomerType.INDIVIDUAL, name="Zoe Pérez"))
    create_service.execute(CreateCustomerInput(customer_type=CustomerType.COMPANY, name="Alpha Eventos"))

    customers = ListCustomersService(db_session).execute()

    assert [customer.name for customer in customers] == ["Alpha Eventos", "Zoe Pérez"]
    assert customers[0].customer_type == CustomerType.COMPANY
    assert customers[0].is_active is True


def test_list_customer_picker_options_service_returns_searchable_customer_fields(db_session):
    customer = CreateCustomerService(db_session).execute(
        CreateCustomerInput(
            customer_type=CustomerType.COMPANY,
            name="Eventos Atlántico",
            company_name="Eventos Atlántico SL",
            tax_id="B12345678",
            phone="+34 600000001",
            email="events@example.com",
            city="La Laguna",
        )
    )

    options = ListCustomerPickerOptionsService(db_session).execute()

    assert len(options) == 1
    assert options[0].id == customer.id
    assert options[0].customer_type == CustomerType.COMPANY
    assert options[0].name == "Eventos Atlántico"
    assert options[0].company_name == "Eventos Atlántico SL"
    assert options[0].tax_id == "B12345678"
    assert options[0].phone == "+34 600000001"
    assert options[0].email == "events@example.com"
    assert options[0].is_active is True


def test_get_customer_for_edit_service_returns_full_customer_data(db_session):
    customer = CreateCustomerService(db_session).execute(
        CreateCustomerInput(
            customer_type=CustomerType.INDIVIDUAL,
            name="María Rodríguez",
            company_name=None,
            tax_id="12345678Z",
            phone="+34 600000000",
            email="maria@example.com",
            address_line_1="Calle Mayor 1",
            address_line_2="Piso 2",
            postal_code="38001",
            city="Santa Cruz de Tenerife",
            country="Spain",
            notes="Frequent customer",
        )
    )

    result = GetCustomerForEditService(db_session).execute(customer.id)

    assert result.id == customer.id
    assert result.customer_type == CustomerType.INDIVIDUAL
    assert result.name == "María Rodríguez"
    assert result.company_name is None
    assert result.tax_id == "12345678Z"
    assert result.phone == "+34 600000000"
    assert result.email == "maria@example.com"
    assert result.address_line_1 == "Calle Mayor 1"
    assert result.address_line_2 == "Piso 2"
    assert result.postal_code == "38001"
    assert result.city == "Santa Cruz de Tenerife"
    assert result.country == "Spain"
    assert result.notes == "Frequent customer"
    assert result.is_active is True


def test_update_customer_service_updates_customer(db_session):
    customer = CreateCustomerService(db_session).execute(
        CreateCustomerInput(
            customer_type=CustomerType.INDIVIDUAL,
            name="María Rodríguez",
            phone="+34 600000000",
        )
    )

    updated = UpdateCustomerService(db_session).execute(
        customer.id,
        UpdateCustomerInput(
            customer_type=CustomerType.COMPANY,
            name="Eventos del Norte",
            company_name="Eventos del Norte SL",
            tax_id="B87654321",
            phone="+34 611111111",
            email="north@example.com",
            address_line_1="Camino Norte 5",
            address_line_2=None,
            postal_code="38300",
            city="La Orotava",
            country="Spain",
            notes="Updated customer",
            is_active=False,
        ),
    )

    assert updated.id == customer.id
    assert updated.customer_type == CustomerType.COMPANY
    assert updated.name == "Eventos del Norte"
    assert updated.company_name == "Eventos del Norte SL"
    assert updated.tax_id == "B87654321"
    assert updated.phone == "+34 611111111"
    assert updated.email == "north@example.com"
    assert updated.address_line_1 == "Camino Norte 5"
    assert updated.address_line_2 is None
    assert updated.postal_code == "38300"
    assert updated.city == "La Orotava"
    assert updated.country == "Spain"
    assert updated.notes == "Updated customer"
    assert updated.is_active is False


def test_customer_services_fail_when_name_is_blank(db_session):
    create_service = CreateCustomerService(db_session)
    update_service = UpdateCustomerService(db_session)

    with pytest.raises(ValueError, match="Customer name is required."):
        create_service.execute(
            CreateCustomerInput(customer_type=CustomerType.INDIVIDUAL, name=" ")
        )

    with pytest.raises(ValueError, match="Customer name is required."):
        update_service.execute(
            999999,
            UpdateCustomerInput(customer_type=CustomerType.INDIVIDUAL, name=" "),
        )


def test_customer_edit_services_fail_when_customer_does_not_exist(db_session):
    with pytest.raises(ValueError, match="Customer not found."):
        GetCustomerForEditService(db_session).execute(999999)

    with pytest.raises(ValueError, match="Customer not found."):
        UpdateCustomerService(db_session).execute(
            999999,
            UpdateCustomerInput(
                customer_type=CustomerType.INDIVIDUAL,
                name="Missing Customer",
            ),
        )
