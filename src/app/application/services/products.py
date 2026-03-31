import re
from decimal import Decimal

import unicodedata
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.application.dto.products import (
    CreateProductInput,
    CreateProductVariantInput,
    ProductListItem,
    ProductVariantListItem,
)
from app.infrastructure.db.models import Product, ProductVariant


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

        generated_variants: list[ProductVariant] = []

        for index, variant_data in enumerate(data.variants, start=1):
            sku = variant_data.sku or self._generate_sku(product.name, product.id, index)

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

        if data.base_price is not None and data.base_price < Decimal("0"):
            raise ValueError("Product base price cannot be negative.")

        provided_skus = [variant.sku for variant in data.variants if variant.sku]
        if len(provided_skus) != len(set(provided_skus)):
            raise ValueError("Variant SKUs must be unique within the request.")

        for index, variant in enumerate(data.variants, start=1):
            self._validate_variant_input(variant, index)

    def _validate_variant_input(self, variant: CreateProductVariantInput, index: int) -> None:
        if variant.price_override is not None and variant.price_override < Decimal("0"):
            raise ValueError(f"Variant #{index} price override cannot be negative.")

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

class ListProductsService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self) -> list[ProductListItem]:
        statement = (
            select(Product)
            .options(selectinload(Product.variants))
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
                    price_override=variant.price_override,
                    is_active=variant.is_active,
                )
                for variant in sorted(product.variants, key=lambda v: v.id)
            ]

            result.append(
                ProductListItem(
                    id=product.id,
                    supplier_id=product.supplier_id,
                    name=product.name,
                    description=product.description,
                    base_price=product.base_price,
                    track_stock=product.track_stock,
                    is_active=product.is_active,
                    variants=variants,
                )
            )

        return result