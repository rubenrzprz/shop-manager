from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.application.dto.orders import (
    CreateOrderInput,
    CreateOrderLineInput,
    OrderLineListItem,
    OrderListItem,
)
from app.domain.enums import DiscountType, OrderStatus
from app.infrastructure.db.models.customers import Customer
from app.infrastructure.db.models.orders import Order, OrderLine
from app.infrastructure.db.models.products import ProductVariant


MAX_MONEY_AMOUNT = Decimal("99999999.99")


class CreateOrderService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, data: CreateOrderInput) -> Order:
        self._validate_order_input(data)
        discount_value = self._money(data.discount_value)

        customer = self._session.get(Customer, data.customer_id)
        if customer is None:
            raise ValueError("Customer not found.")
        if not customer.is_active:
            raise ValueError("Customer must be active to create an order.")

        prepared_lines = self._prepare_order_lines(data.lines)
        subtotal = self._money(sum(line.line_total for line in prepared_lines))
        self._validate_money_upper_bound(
            subtotal,
            "Order subtotal cannot be greater than 99999999.99.",
        )
        self._validate_discount_bounds(
            subtotal,
            data.discount_type,
            discount_value,
        )
        discount_amount = self._discount_amount(
            subtotal,
            data.discount_type,
            discount_value,
        )
        total_amount = self._money(subtotal - discount_amount)
        self._validate_money_upper_bound(
            discount_amount,
            "Order discount amount cannot be greater than 99999999.99.",
        )
        self._validate_money_upper_bound(
            total_amount,
            "Order total cannot be greater than 99999999.99.",
        )

        order = Order(
            order_number=f"PENDING-{uuid4()}",
            customer_id=customer.id,
            status=OrderStatus.DRAFT,
            order_date=data.order_date,
            deadline=data.deadline,
            discount_type=data.discount_type,
            discount_value=discount_value,
            notes=data.notes,
        )

        self._session.add(order)
        self._session.flush()
        order.order_number = self._order_number(order.id)

        order_lines: list[OrderLine] = []

        for prepared_line in prepared_lines:
            line = OrderLine(
                order_id=order.id,
                product_variant_id=prepared_line.variant.id,
                quantity=prepared_line.input.quantity,
                unit_price=prepared_line.unit_price,
                line_total=prepared_line.line_total,
                notes=prepared_line.input.notes,
            )
            self._session.add(line)
            order_lines.append(line)

        order.subtotal_amount = subtotal
        order.discount_amount = discount_amount
        order.total_amount = total_amount

        self._session.flush()
        order.lines = order_lines

        return order

    def _validate_order_input(self, data: CreateOrderInput) -> None:
        if not data.lines:
            raise ValueError("An order must have at least one line.")

        if data.deadline is not None and data.deadline < data.order_date:
            raise ValueError("Order deadline cannot be earlier than the order date.")

        self._validate_decimal_amount(
            data.discount_value,
            "Discount value must be a finite number.",
            "Discount value cannot be negative.",
        )

        if data.discount_type == DiscountType.NONE and data.discount_value != Decimal("0.00"):
            raise ValueError("Discount value must be zero when discount type is NONE.")

        if data.discount_type == DiscountType.PERCENTAGE and data.discount_value > Decimal("100"):
            raise ValueError("Percentage discount cannot be greater than 100.")

        for index, line in enumerate(data.lines, start=1):
            if line.quantity <= 0:
                raise ValueError(f"Line #{index} quantity must be positive.")

            self._validate_decimal_amount(
                line.unit_price,
                f"Line #{index} unit price must be a finite number.",
                f"Line #{index} unit price cannot be negative.",
            )

    def _prepare_order_lines(
        self,
        lines: list[CreateOrderLineInput],
    ) -> list["_PreparedOrderLine"]:
        prepared_lines: list[_PreparedOrderLine] = []

        for index, line_data in enumerate(lines, start=1):
            variant = self._load_valid_variant(line_data.product_variant_id, index)
            unit_price = self._line_unit_price(line_data, variant, index)
            line_total = self._money(unit_price * line_data.quantity)
            self._validate_money_upper_bound(
                line_total,
                f"Line #{index} total cannot be greater than 99999999.99.",
            )
            prepared_lines.append(
                _PreparedOrderLine(
                    input=line_data,
                    variant=variant,
                    unit_price=unit_price,
                    line_total=line_total,
                )
            )

        return prepared_lines

    def _load_valid_variant(self, variant_id: int, line_index: int) -> ProductVariant:
        variant = self._session.get(
            ProductVariant,
            variant_id,
            options=[joinedload(ProductVariant.product)],
        )

        if variant is None:
            raise ValueError(f"Line #{line_index} product variant not found.")
        if not variant.is_active:
            raise ValueError(f"Line #{line_index} product variant must be active.")
        if not variant.product.is_active:
            raise ValueError(f"Line #{line_index} product must be active.")

        return variant

    def _line_unit_price(
        self,
        line_data: CreateOrderLineInput,
        variant: ProductVariant,
        line_index: int,
    ) -> Decimal:
        if line_data.unit_price is not None:
            unit_price = self._money(line_data.unit_price)
            self._validate_money_upper_bound(
                unit_price,
                f"Line #{line_index} unit price cannot be greater than 99999999.99.",
            )
            return unit_price

        inferred_price = variant.price_override if variant.price_override is not None else variant.product.base_price
        if inferred_price is None:
            raise ValueError(f"Line #{line_index} unit price is required.")

        unit_price = self._money(inferred_price)
        self._validate_money_upper_bound(
            unit_price,
            f"Line #{line_index} unit price cannot be greater than 99999999.99.",
        )
        return unit_price

    @staticmethod
    def _order_number(order_id: int) -> str:
        return f"ORD-{order_id:06d}"

    @classmethod
    def _discount_amount(
        cls,
        subtotal: Decimal,
        discount_type: DiscountType,
        discount_value: Decimal,
    ) -> Decimal:
        if discount_type == DiscountType.NONE:
            return Decimal("0.00")

        if discount_type == DiscountType.FIXED:
            return min(cls._money(discount_value), subtotal)

        if discount_type == DiscountType.PERCENTAGE:
            return min(cls._money(subtotal * (discount_value / Decimal("100"))), subtotal)

        raise ValueError("Unsupported discount type.")

    @staticmethod
    def _validate_discount_bounds(
        subtotal: Decimal,
        discount_type: DiscountType,
        discount_value: Decimal,
    ) -> None:
        if discount_type == DiscountType.FIXED and discount_value > subtotal:
            raise ValueError("Fixed discount cannot be greater than the subtotal.")

    @staticmethod
    def _validate_decimal_amount(
        value: Decimal | None,
        non_finite_message: str,
        negative_message: str,
    ) -> None:
        if value is None:
            return

        if not value.is_finite():
            raise ValueError(non_finite_message)

        if value < Decimal("0"):
            raise ValueError(negative_message)

    @staticmethod
    def _validate_money_upper_bound(value: Decimal, message: str) -> None:
        if value > MAX_MONEY_AMOUNT:
            raise ValueError(message)

    @staticmethod
    def _money(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class _PreparedOrderLine:
    input: CreateOrderLineInput
    variant: ProductVariant
    unit_price: Decimal
    line_total: Decimal


class ListOrdersService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self) -> list[OrderListItem]:
        statement = (
            select(Order)
            .options(
                joinedload(Order.customer),
                selectinload(Order.lines)
                .joinedload(OrderLine.product_variant)
                .joinedload(ProductVariant.product),
            )
            .order_by(Order.order_date.desc(), Order.id.desc())
        )
        orders = self._session.scalars(statement).all()

        return [
            OrderListItem(
                id=order.id,
                order_number=order.order_number,
                customer_id=order.customer_id,
                customer_name=order.customer.name,
                status=order.status,
                order_date=order.order_date,
                deadline=order.deadline,
                subtotal_amount=order.subtotal_amount,
                discount_type=order.discount_type,
                discount_value=order.discount_value,
                discount_amount=order.discount_amount,
                total_amount=order.total_amount,
                lines=[
                    OrderLineListItem(
                        id=line.id,
                        product_variant_id=line.product_variant_id,
                        product_name=line.product_variant.product.name,
                        sku=line.product_variant.sku,
                        quantity=line.quantity,
                        unit_price=line.unit_price,
                        line_total=line.line_total,
                    )
                    for line in sorted(order.lines, key=lambda order_line: order_line.id)
                ],
            )
            for order in orders
        ]
