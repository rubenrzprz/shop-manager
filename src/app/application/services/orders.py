from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.application.dto.orders import (
    CreateOrderInput,
    CreateOrderLineInput,
    OrderEditItem,
    OrderLineListItem,
    OrderListItem,
    UpdateOrderLineInput,
    UpdateOrderInput,
)
from app.application.services.settings import ApplicationSettingsService
from app.application.services.tasks import (
    ACTIVE_ORDER_FOLLOW_UP_STATUSES,
    GenerateOrderFollowUpTasksService,
)
from app.domain.enums import DiscountType, OrderStatus
from app.infrastructure.db.models.customers import Customer
from app.infrastructure.db.models.orders import Order, OrderLine
from app.infrastructure.db.models.products import ProductVariant

MAX_MONEY_AMOUNT = Decimal("99999999.99")
MAX_ORDER_LINE_QUANTITY = 999999
SIMPLE_EDITABLE_ORDER_STATUSES = {
    OrderStatus.DRAFT,
    OrderStatus.CONFIRMED,
    OrderStatus.IN_PROGRESS,
    OrderStatus.READY,
}
STRICT_FULL_EDIT_ORDER_STATUSES = {
    OrderStatus.DRAFT,
    OrderStatus.CONFIRMED,
    OrderStatus.IN_PROGRESS,
}
ACTIVE_ORDER_STATUSES = {
    OrderStatus.DRAFT,
    OrderStatus.CONFIRMED,
    OrderStatus.IN_PROGRESS,
    OrderStatus.READY,
}


class OrderEditCapability(StrEnum):
    FULL = "full"
    READY_LIMITED = "ready_limited"
    NOTES_ONLY = "notes_only"
    NONE = "none"


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
        GenerateOrderFollowUpTasksService(self._session).ensure_open_follow_up_for_order(order)

        return order

    def _validate_order_input(self, data: CreateOrderInput | UpdateOrderInput) -> None:
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

            if line.quantity > MAX_ORDER_LINE_QUANTITY:
                raise ValueError(f"Line #{index} quantity cannot be greater than 999999.")

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
            prepared_lines.append(self._prepare_order_line(line_data, index))

        return prepared_lines

    def _prepare_order_line(
        self,
        line_data: CreateOrderLineInput,
        line_index: int,
    ) -> "_PreparedOrderLine":
        variant = self._load_valid_variant(line_data.product_variant_id, line_index)
        unit_price = self._line_unit_price(line_data, variant, line_index)
        line_total = self._money(unit_price * line_data.quantity)
        self._validate_money_upper_bound(
            line_total,
            f"Line #{line_index} total cannot be greater than 99999999.99.",
        )

        return _PreparedOrderLine(
            input=line_data,
            variant=variant,
            unit_price=unit_price,
            line_total=line_total,
        )

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

        inferred_price = (
            variant.price_override
            if variant.price_override is not None
            else variant.product.base_price
        )
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
    variant: ProductVariant | None
    unit_price: Decimal
    line_total: Decimal


class GetOrderForEditService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, order_id: int) -> OrderEditItem:
        order = self._session.get(
            Order,
            order_id,
            options=[
                joinedload(Order.customer),
                selectinload(Order.lines)
                .joinedload(OrderLine.product_variant)
                .joinedload(ProductVariant.product),
            ],
        )

        if order is None:
            raise ValueError("Order not found.")

        return OrderEditItem(
            id=order.id,
            order_number=order.order_number,
            customer_id=order.customer_id,
            customer_name=order.customer.name,
            status=order.status,
            order_date=order.order_date,
            deadline=order.deadline,
            discount_type=order.discount_type,
            discount_value=order.discount_value,
            notes=order.notes,
            lines=[
                OrderLineListItem(
                    id=line.id,
                    product_variant_id=line.product_variant_id,
                    product_name=line.product_variant.product.name,
                    sku=line.product_variant.sku,
                    variant_name=line.product_variant.variant_name,
                    size=line.product_variant.size,
                    color=line.product_variant.color,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                    line_total=line.line_total,
                    notes=line.notes,
                )
                for line in sorted(order.lines, key=lambda order_line: order_line.id)
            ],
        )


class UpdateOrderService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._create_service = CreateOrderService(session)

    def execute(self, order_id: int, data: UpdateOrderInput) -> Order:
        order = self._session.get(
            Order,
            order_id,
            options=[selectinload(Order.lines)],
        )
        if order is None:
            raise ValueError("Order not found.")

        edit_capability = self.order_edit_capability(order.status)
        if edit_capability == OrderEditCapability.NONE:
            raise ValueError(self.order_edit_rejection_message(order.status))

        if edit_capability == OrderEditCapability.NOTES_ONLY:
            self._validate_notes_only_update(order, data)
            order.notes = data.notes
            self._session.flush()
            return order

        self._create_service._validate_order_input(data)
        discount_value = self._create_service._money(data.discount_value)

        if edit_capability == OrderEditCapability.READY_LIMITED:
            self._validate_ready_limited_update(order, data)
            self._apply_ready_limited_update(order, data, discount_value)
            self._session.flush()
            return order

        customer = self._session.get(Customer, data.customer_id)
        if customer is None:
            raise ValueError("Customer not found.")
        if not customer.is_active:
            raise ValueError("Customer must be active to update an order.")

        prepared_lines = self._prepare_order_lines(order, data.lines)
        subtotal = self._create_service._money(sum(line.line_total for line in prepared_lines))
        self._create_service._validate_money_upper_bound(
            subtotal,
            "Order subtotal cannot be greater than 99999999.99.",
        )
        self._create_service._validate_discount_bounds(
            subtotal,
            data.discount_type,
            discount_value,
        )
        discount_amount = self._create_service._discount_amount(
            subtotal,
            data.discount_type,
            discount_value,
        )
        total_amount = self._create_service._money(subtotal - discount_amount)
        self._create_service._validate_money_upper_bound(
            discount_amount,
            "Order discount amount cannot be greater than 99999999.99.",
        )
        self._create_service._validate_money_upper_bound(
            total_amount,
            "Order total cannot be greater than 99999999.99.",
        )

        order.customer_id = customer.id
        order.order_date = data.order_date
        order.deadline = data.deadline
        order.discount_type = data.discount_type
        order.discount_value = discount_value
        order.discount_amount = discount_amount
        order.subtotal_amount = subtotal
        order.total_amount = total_amount
        order.notes = data.notes

        order.lines.clear()
        self._session.flush()

        for prepared_line in prepared_lines:
            order.lines.append(
                OrderLine(
                    product_variant_id=prepared_line.input.product_variant_id,
                    quantity=prepared_line.input.quantity,
                    unit_price=prepared_line.unit_price,
                    line_total=prepared_line.line_total,
                    notes=prepared_line.input.notes,
                )
            )

        self._session.flush()

        return order

    @staticmethod
    def _order_edit_capability(
        status: OrderStatus, *, strict_order_workflow_enabled: bool
    ) -> OrderEditCapability:
        if not strict_order_workflow_enabled:
            if status in SIMPLE_EDITABLE_ORDER_STATUSES:
                return OrderEditCapability.FULL
            if status in {OrderStatus.COMPLETED, OrderStatus.CANCELLED}:
                return OrderEditCapability.NOTES_ONLY
            return OrderEditCapability.NONE

        if status in STRICT_FULL_EDIT_ORDER_STATUSES:
            return OrderEditCapability.FULL
        if status == OrderStatus.READY:
            return OrderEditCapability.READY_LIMITED
        if status in {OrderStatus.COMPLETED, OrderStatus.CANCELLED}:
            return OrderEditCapability.NOTES_ONLY

        return OrderEditCapability.NONE

    def order_edit_capability(self, status: OrderStatus) -> OrderEditCapability:
        return self._order_edit_capability(
            status,
            strict_order_workflow_enabled=ApplicationSettingsService(
                self._session
            ).strict_order_workflow_enabled(),
        )

    def can_edit_full_order(self, status: OrderStatus) -> bool:
        return self.order_edit_capability(status) == OrderEditCapability.FULL

    def can_edit_order(self, status: OrderStatus) -> bool:
        return self.order_edit_capability(status) != OrderEditCapability.NONE

    def order_edit_rejection_message(self, status: OrderStatus) -> str | None:
        if self.can_edit_order(status):
            return None

        if not ApplicationSettingsService(self._session).strict_order_workflow_enabled():
            return "Only active orders can be edited."

        return "This order status cannot be edited."

    def full_order_edit_rejection_message(self, status: OrderStatus) -> str | None:
        if self.can_edit_full_order(status):
            return None

        capability = self.order_edit_capability(status)
        if capability == OrderEditCapability.READY_LIMITED:
            return "Ready orders only allow deadline, discount, and notes changes."
        if capability == OrderEditCapability.NOTES_ONLY:
            return "Completed and cancelled orders only allow notes changes."

        return self.order_edit_rejection_message(status)

    def _apply_ready_limited_update(
        self,
        order: Order,
        data: UpdateOrderInput,
        discount_value: Decimal,
    ) -> None:
        subtotal = self._create_service._money(sum(line.line_total for line in order.lines))
        self._create_service._validate_discount_bounds(
            subtotal,
            data.discount_type,
            discount_value,
        )
        discount_amount = self._create_service._discount_amount(
            subtotal,
            data.discount_type,
            discount_value,
        )
        total_amount = self._create_service._money(subtotal - discount_amount)
        self._create_service._validate_money_upper_bound(
            discount_amount,
            "Order discount amount cannot be greater than 99999999.99.",
        )
        self._create_service._validate_money_upper_bound(
            total_amount,
            "Order total cannot be greater than 99999999.99.",
        )

        order.deadline = data.deadline
        order.discount_type = data.discount_type
        order.discount_value = discount_value
        order.discount_amount = discount_amount
        order.subtotal_amount = subtotal
        order.total_amount = total_amount
        order.notes = data.notes

    def _validate_ready_limited_update(self, order: Order, data: UpdateOrderInput) -> None:
        if order.customer_id != data.customer_id:
            raise ValueError("Ready orders cannot change customer.")
        if order.order_date != data.order_date:
            raise ValueError("Ready orders cannot change order date.")
        if not self._order_lines_match_input(order, data.lines):
            raise ValueError("Ready orders cannot change order lines.")

    def _validate_notes_only_update(self, order: Order, data: UpdateOrderInput) -> None:
        if order.customer_id != data.customer_id:
            raise ValueError("Completed and cancelled orders cannot change customer.")
        if order.order_date != data.order_date:
            raise ValueError("Completed and cancelled orders cannot change order date.")
        if order.deadline != data.deadline:
            raise ValueError("Completed and cancelled orders cannot change deadline.")
        if order.discount_type != data.discount_type:
            raise ValueError("Completed and cancelled orders cannot change discount.")
        if self._create_service._money(order.discount_value) != self._create_service._money(
            data.discount_value
        ):
            raise ValueError("Completed and cancelled orders cannot change discount.")
        if not self._order_lines_match_input(order, data.lines):
            raise ValueError("Completed and cancelled orders cannot change order lines.")

    def _order_lines_match_input(
        self,
        order: Order,
        lines: list[UpdateOrderLineInput],
    ) -> bool:
        existing_lines = sorted(order.lines, key=lambda line: line.id)
        input_lines = sorted(lines, key=lambda line: line.order_line_id or 0)
        if len(existing_lines) != len(input_lines):
            return False

        for existing_line, input_line in zip(existing_lines, input_lines, strict=True):
            if existing_line.id != input_line.order_line_id:
                return False
            if existing_line.product_variant_id != input_line.product_variant_id:
                return False
            if existing_line.quantity != input_line.quantity:
                return False
            input_unit_price = (
                input_line.unit_price
                if input_line.unit_price is not None
                else existing_line.unit_price
            )
            if self._create_service._money(existing_line.unit_price) != self._create_service._money(
                input_unit_price
            ):
                return False
            if existing_line.notes != input_line.notes:
                return False

        return True

    def _prepare_order_lines(
        self,
        order: Order,
        lines: list[UpdateOrderLineInput],
    ) -> list["_PreparedOrderLine"]:
        existing_lines_by_id = {line.id: line for line in order.lines}
        prepared_lines: list[_PreparedOrderLine] = []

        for index, line_data in enumerate(lines, start=1):
            existing_line = (
                existing_lines_by_id.get(line_data.order_line_id)
                if line_data.order_line_id is not None
                else None
            )

            if (
                existing_line is not None
                and existing_line.product_variant_id == line_data.product_variant_id
            ):
                unit_price = self._line_unit_price_for_existing_line(line_data, existing_line)
                line_total = self._create_service._money(unit_price * line_data.quantity)
                self._create_service._validate_money_upper_bound(
                    line_total,
                    f"Line #{index} total cannot be greater than 99999999.99.",
                )
                prepared_lines.append(
                    _PreparedOrderLine(
                        input=CreateOrderLineInput(
                            product_variant_id=line_data.product_variant_id,
                            quantity=line_data.quantity,
                            unit_price=unit_price,
                            notes=line_data.notes,
                        ),
                        variant=None,
                        unit_price=unit_price,
                        line_total=line_total,
                    )
                )
                continue

            prepared_lines.append(
                self._create_service._prepare_order_line(
                    CreateOrderLineInput(
                        product_variant_id=line_data.product_variant_id,
                        quantity=line_data.quantity,
                        unit_price=line_data.unit_price,
                        notes=line_data.notes,
                    ),
                    index,
                )
            )

        return prepared_lines

    def _line_unit_price_for_existing_line(
        self,
        line_data: UpdateOrderLineInput,
        existing_line: OrderLine,
    ) -> Decimal:
        unit_price = (
            line_data.unit_price if line_data.unit_price is not None else existing_line.unit_price
        )
        unit_price = self._create_service._money(unit_price)
        self._create_service._validate_money_upper_bound(
            unit_price,
            "Line unit price cannot be greater than 99999999.99.",
        )

        return unit_price


class UpdateOrderStatusService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, order_id: int, target_status: OrderStatus) -> Order:
        order = self._session.get(Order, order_id)
        if order is None:
            raise ValueError("Order not found.")

        if not self.can_transition(order.status, target_status):
            raise ValueError(
                f"Cannot transition order from {order.status.value} to {target_status.value}."
            )

        order.status = target_status
        if target_status == OrderStatus.COMPLETED:
            order.completed_at = datetime.now(UTC)
        else:
            order.completed_at = None

        self._session.flush()
        if target_status in ACTIVE_ORDER_FOLLOW_UP_STATUSES:
            GenerateOrderFollowUpTasksService(self._session).ensure_open_follow_up_for_order(order)

        return order

    def can_transition(
        self,
        current_status: OrderStatus,
        target_status: OrderStatus,
    ) -> bool:
        return self._can_transition(
            current_status,
            target_status,
            ApplicationSettingsService(self._session).enabled_order_statuses(),
        )

    @staticmethod
    def _can_transition(
        current_status: OrderStatus,
        target_status: OrderStatus,
        enabled_statuses: tuple[OrderStatus, ...],
    ) -> bool:
        if target_status == OrderStatus.CANCELLED:
            return current_status in ACTIVE_ORDER_STATUSES
        if current_status == OrderStatus.CANCELLED and target_status == OrderStatus.DRAFT:
            return True

        return target_status in {
            UpdateOrderStatusService._next_forward_status(current_status, enabled_statuses),
            UpdateOrderStatusService._previous_status(current_status, enabled_statuses),
        }

    def next_forward_status(self, current_status: OrderStatus) -> OrderStatus | None:
        return self._next_forward_status(
            current_status,
            ApplicationSettingsService(self._session).enabled_order_statuses(),
        )

    @staticmethod
    def _next_forward_status(
        current_status: OrderStatus,
        enabled_statuses: tuple[OrderStatus, ...],
    ) -> OrderStatus | None:
        if current_status in {OrderStatus.COMPLETED, OrderStatus.CANCELLED}:
            return None
        if current_status not in enabled_statuses:
            return None

        current_index = enabled_statuses.index(current_status)
        for status in enabled_statuses[current_index + 1 :]:
            if status != OrderStatus.CANCELLED:
                return status

        return None

    def previous_status(self, current_status: OrderStatus) -> OrderStatus | None:
        return self._previous_status(
            current_status,
            ApplicationSettingsService(self._session).enabled_order_statuses(),
        )

    @staticmethod
    def _previous_status(
        current_status: OrderStatus,
        enabled_statuses: tuple[OrderStatus, ...],
    ) -> OrderStatus | None:
        if current_status in {OrderStatus.DRAFT, OrderStatus.CANCELLED}:
            return None
        if current_status not in enabled_statuses:
            return None

        current_index = enabled_statuses.index(current_status)
        for status in reversed(enabled_statuses[:current_index]):
            if status != OrderStatus.CANCELLED:
                return status

        return None


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
                        variant_name=line.product_variant.variant_name,
                        size=line.product_variant.size,
                        color=line.product_variant.color,
                        quantity=line.quantity,
                        unit_price=line.unit_price,
                        line_total=line.line_total,
                        notes=line.notes,
                    )
                    for line in sorted(order.lines, key=lambda order_line: order_line.id)
                ],
            )
            for order in orders
        ]
