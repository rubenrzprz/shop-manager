import re
from decimal import Decimal

import unicodedata
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload, joinedload

from app.application.dto.products import (
    CreateProductInput,
    CreateProductVariantInput,
    ProductEditItem,
    ProductListItem,
    ProductVariantEditItem,
    ProductVariantListItem,
    SupplierOption,
    UNSET,
    UpdateProductInput,
    UpdateProductVariantInput,
)
from app.infrastructure.db.models import Product, ProductVariant
from app.infrastructure.db.models.suppliers import Supplier


class CreateProductService:
    def __init__(self, session: Session):
        self._session = session

    def execute(self, data: CreateProductInput) -> Product:
        self._validate_product_input(data)

        product = Product(
            supplier_id=data.supplier_id,
            name=data.name.strip(),
            description=data.description,
            base_price=data.base_price,
            track_stock=data.track_stock,
            is_active=data.is_active,
        )

        self._session.add(product)
        self._session.flush()
        try:
            self._validate_final_variant_skus(product.name, product.id, data.variants)
        except ValueError:
            self._session.delete(product)
            self._session.flush()
            raise

        generated_variants: list[ProductVariant] = []

        for index, variant_data in enumerate(data.variants, start=1):
            sku = self._normalize_sku(variant_data.sku) or self._generate_sku(
                product.name,
                product.id,
                index,
            )

            variant = ProductVariant(
                product_id=product.id,
                sku=sku,
                size=variant_data.size,
                color=variant_data.color,
                variant_name=variant_data.variant_name,
                description=variant_data.description,
                price_override=variant_data.price_override,
                stock_current=variant_data.stock_current,
                stock_minimum=variant_data.stock_minimum,
                is_active=variant_data.is_active,
            )

            self._session.add(variant)
            generated_variants.append(variant)

        self._session.flush()

        product.variants = generated_variants
        return product

    def _validate_product_input(self, data: CreateProductInput) -> None:
        if not data.name or not data.name.strip():
            raise ValueError("Product name is required.")

        if not data.variants:
            raise ValueError("A product must have at least one variant.")

        self._validate_decimal_amount(
            data.base_price,
            "Product base price must be a finite number.",
            "Product base price cannot be negative.",
        )

        provided_skus: list[str] = []
        for index, variant in enumerate(data.variants, start=1):
            normalized_sku = self._normalize_sku(variant.sku)
            if normalized_sku is not None:
                provided_skus.append(normalized_sku)
            self._validate_variant_input(variant, index)

        if len(provided_skus) != len(set(provided_skus)):
            raise ValueError("Variant SKUs must be unique within the request.")

    def _validate_final_variant_skus(
        self,
        product_name: str,
        product_id: int,
        variants: list[CreateProductVariantInput],
    ) -> None:
        final_skus = [
            self._normalize_sku(variant.sku) or self._generate_sku(product_name, product_id, index)
            for index, variant in enumerate(variants, start=1)
        ]

        if len(final_skus) != len(set(final_skus)):
            raise ValueError("Variant SKUs must be unique within the request.")

    def _validate_variant_input(self, variant: CreateProductVariantInput, index: int) -> None:
        normalized_sku = self._normalize_sku(variant.sku)
        if variant.sku is not None and normalized_sku is None:
            raise ValueError(f"Variant #{index} SKU cannot be blank.")

        self._validate_decimal_amount(
            variant.price_override,
            f"Variant #{index} price override must be a finite number.",
            f"Variant #{index} price override cannot be negative.",
        )

        if variant.stock_current is not None and variant.stock_current < 0:
            raise ValueError(f"Variant #{index} stock_current cannot be negative.")

        if variant.stock_minimum is not None and variant.stock_minimum < 0:
            raise ValueError(f"Variant #{index} stock_minimum cannot be negative.")

    def _generate_prefix(self, name: str) -> str:
        if not name:
            return "PRD"

        # Normalize accents (á → a)
        normalized = unicodedata.normalize("NFKD", name)
        ascii_name = normalized.encode("ascii", "ignore").decode("ascii")

        if not ascii_name.strip():
            return "PRD"

        # Extract first word
        first_word = ascii_name.strip().split()[0]

        # Remove non letters
        first_word = re.sub(r"[^A-Za-z]", "", first_word)

        if not first_word:
            return "PRD"

        prefix = first_word[:3].upper()

        # Pad if too short
        if len(prefix) < 3:
            prefix = prefix.ljust(3, "X")

        return prefix

    def _generate_sku(self, product_name: str, product_id: int, variant_index: int) -> str:
        prefix = self._generate_prefix(product_name)
        return f"{prefix}-{product_id:04d}-{variant_index:02d}"

    @staticmethod
    def _normalize_sku(raw_sku: str | None) -> str | None:
        if raw_sku is None:
            return None

        normalized = raw_sku.strip()
        return normalized or None

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

class ListProductsService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self) -> list[ProductListItem]:
        statement = (
            select(Product)
            .options(
                joinedload(Product.supplier),
                selectinload(Product.variants),
            )
            .order_by(Product.id)
        )

        products = self._session.scalars(statement).all()

        result: list[ProductListItem] = []

        for product in products:
            variants = [
                ProductVariantListItem(
                    id=variant.id,
                    sku=variant.sku,
                    size=variant.size,
                    color=variant.color,
                    variant_name=variant.variant_name,
                    description=variant.description,
                    price_override=variant.price_override,
                    is_active=variant.is_active,
                )
                for variant in sorted(product.variants, key=lambda v: v.id)
            ]

            result.append(
                ProductListItem(
                    id=product.id,
                    supplier_id=product.supplier_id,
                    supplier_name=product.supplier.name if product.supplier else None,
                    name=product.name,
                    description=product.description,
                    base_price=product.base_price,
                    track_stock=product.track_stock,
                    is_active=product.is_active,
                    variants=variants,
                )
            )

        return result


class ListProductFormSuppliersService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self) -> list[SupplierOption]:
        statement = select(Supplier).order_by(Supplier.name)
        suppliers = self._session.scalars(statement).all()

        return [
            SupplierOption(
                id=supplier.id,
                name=supplier.name,
            )
            for supplier in suppliers
        ]


class GetProductForEditService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, product_id: int) -> ProductEditItem:
        product = self._session.get(
            Product,
            product_id,
            options=[selectinload(Product.variants)],
        )

        if product is None:
            raise ValueError("Product not found.")

        default_variant = self._default_variant(product)

        return ProductEditItem(
            id=product.id,
            supplier_id=product.supplier_id,
            name=product.name,
            description=product.description,
            base_price=product.base_price,
            track_stock=product.track_stock,
            is_active=product.is_active,
            default_variant=ProductVariantEditItem(
                id=default_variant.id,
                sku=default_variant.sku,
                size=default_variant.size,
                color=default_variant.color,
                variant_name=default_variant.variant_name,
                description=default_variant.description,
                price_override=default_variant.price_override,
                is_active=default_variant.is_active,
            ),
        )

    @staticmethod
    def _default_variant(product: Product) -> ProductVariant:
        variants = sorted(product.variants, key=lambda variant: variant.id)

        if not variants:
            raise ValueError("Product has no variants.")

        return variants[0]


class UpdateProductService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, product_id: int, data: UpdateProductInput) -> Product:
        self._validate_product_input(data)

        product = self._session.get(
            Product,
            product_id,
            options=[selectinload(Product.variants)],
        )

        if product is None:
            raise ValueError("Product not found.")

        if data.supplier_id is not UNSET:
            product.supplier_id = data.supplier_id

        if data.name is not UNSET:
            product.name = data.name.strip()

        if data.description is not UNSET:
            product.description = data.description

        if data.base_price is not UNSET:
            product.base_price = data.base_price

        if data.track_stock is not UNSET:
            product.track_stock = data.track_stock

        if data.default_variant is not None:
            variant = self._find_product_variant(product, data.default_variant.variant_id)

            if data.default_variant.size is not UNSET:
                variant.size = data.default_variant.size

            if data.default_variant.color is not UNSET:
                variant.color = data.default_variant.color

            if data.default_variant.variant_name is not UNSET:
                variant.variant_name = data.default_variant.variant_name

            if data.default_variant.description is not UNSET:
                variant.description = data.default_variant.description

            if data.default_variant.price_override is not UNSET:
                variant.price_override = data.default_variant.price_override

        self._session.flush()

        return product

    def _validate_product_input(self, data: UpdateProductInput) -> None:
        if data.name is not UNSET and not data.name.strip():
            raise ValueError("Product name is required.")

        if data.base_price is not UNSET:
            CreateProductService._validate_decimal_amount(
                data.base_price,
                "Product base price must be a finite number.",
                "Product base price cannot be negative.",
            )

        if data.default_variant is not None:
            self._validate_variant_input(data.default_variant)

    def _validate_variant_input(self, variant: UpdateProductVariantInput) -> None:
        if variant.price_override is not UNSET:
            CreateProductService._validate_decimal_amount(
                variant.price_override,
                "Default variant price override must be a finite number.",
                "Default variant price override cannot be negative.",
            )

    @staticmethod
    def _find_product_variant(product: Product, variant_id: int) -> ProductVariant:
        for variant in product.variants:
            if variant.id == variant_id:
                return variant

        raise ValueError("Product variant not found.")


class ProductStatusService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, product_id: int, is_active: bool) -> Product:
        product = self._session.get(Product, product_id)

        if product is None:
            raise ValueError("Product not found.")

        if product.is_active == is_active:
            status = "active" if is_active else "inactive"
            raise ValueError(f"Product is already {status}.")

        product.is_active = is_active
        self._session.flush()

        return product
