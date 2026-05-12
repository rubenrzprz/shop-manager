from enum import StrEnum


class CustomerType(StrEnum):
    INDIVIDUAL = "INDIVIDUAL"
    COMPANY = "COMPANY"


class DiscountType(StrEnum):
    NONE = "NONE"
    PERCENTAGE = "PERCENTAGE"
    FIXED = "FIXED"


class OrderStatus(StrEnum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    IN_PROGRESS = "IN_PROGRESS"
    READY = "READY"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ShipmentStatus(StrEnum):
    PENDING = "PENDING"
    PREPARING = "PREPARING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class OrderSupplierStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TaskRecurrenceType(StrEnum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class TaskMonthlyRecurrenceRule(StrEnum):
    FIRST_DAY_OF_MONTH = "FIRST_DAY_OF_MONTH"
    DAY_OF_MONTH = "DAY_OF_MONTH"
    SPECIFIC_DAY_OF_MONTH = "SPECIFIC_DAY_OF_MONTH"
    LAST_DAY_OF_MONTH = "LAST_DAY_OF_MONTH"


class TaskSeriesUpdateScope(StrEnum):
    OCCURRENCE = "OCCURRENCE"
    FUTURE = "FUTURE"
    SERIES = "SERIES"


class StockMovementType(StrEnum):
    IN = "IN"
    OUT = "OUT"
    ADJUSTMENT = "ADJUSTMENT"


class StockReferenceType(StrEnum):
    ORDER = "ORDER"
    MANUAL = "MANUAL"
    IMPORT = "IMPORT"
    INITIAL_LOAD = "INITIAL_LOAD"
    RETURN = "RETURN"
