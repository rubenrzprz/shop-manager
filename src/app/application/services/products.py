import re
from decimal import Decimal

import unicodedata
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session, selectinload, joinedload

from app.application.dto.products import (
    CreateProductInput,
    ProductCategorySummary,
    CreateProductVariantInput,
    ProductEditItem,
    ProductListFilters,
    ProductListItem,
    ProductVariantPickerItem,
    ProductVariantEditItem,
    ProductVariantListItem,
    SupplierOption,
    UNSET,
    UpdateProductInput,
    UpdateProductVariantInput,
)
from app.infrastructure.db.models import Product, ProductCategory, ProductVariant
from app.infrastructure.db.models.products import product_category_assignments
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
            is_active=data.is_active and any(variant.is_active for variant in data.variants),
        )
        product.categories = self._load_categories(data.category_ids)

        self._session.add(product)
        self._session.flush()
        self._set_category_order(product.id, data.category_ids)
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

        if len(data.category_ids) != len(set(data.category_ids)):
            raise ValueError("Product categories must be unique.")

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

    def _load_categories(
        self,
        category_ids: list[int],
        allow_inactive_category_ids: set[int] | None = None,
    ) -> list[ProductCategory]:
        if not category_ids:
            return []

        allowed_inactive_ids = allow_inactive_category_ids or set()
        categories = self._session.scalars(
            select(ProductCategory).where(ProductCategory.id.in_(category_ids))
        ).all()
        categories_by_id = {category.id: category for category in categories}

        if set(category_ids) != set(categories_by_id):
            raise ValueError("Product category not found.")

        inactive_category = next(
            (
                category
                for category in categories
                if not category.is_active and category.id not in allowed_inactive_ids
            ),
            None,
        )
        if inactive_category is not None:
            raise ValueError("Product category must be active.")

        return [categories_by_id[category_id] for category_id in category_ids]

    def _set_category_order(self, product_id: int, category_ids: list[int]) -> None:
        for sort_order, category_id in enumerate(category_ids):
            self._session.execute(
                update(product_category_assignments)
                .where(product_category_assignments.c.product_id == product_id)
                .where(product_category_assignments.c.category_id == category_id)
                .values(sort_order=sort_order)
            )

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

    def execute(self, filters: ProductListFilters | None = None) -> list[ProductListItem]:
        statement = (
            select(Product)
            .options(
                joinedload(Product.supplier),
                selectinload(Product.variants),
                selectinload(Product.categories),
            )
            .order_by(Product.id)
        )
        filters = filters or ProductListFilters()
        statement = self._apply_filters(statement, filters)

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
                    stock_current=variant.stock_current,
                    stock_minimum=variant.stock_minimum,
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
                    categories=self._category_summaries(product),
                    variants=variants,
                )
            )

        return result

    @staticmethod
    def _apply_filters(statement, filters: ProductListFilters):
        if filters.category_id is not None and filters.uncategorized_only:
            raise ValueError("Choose either a product category or uncategorized products.")

        if filters.category_id is not None:
            statement = statement.where(
                Product.categories.any(ProductCategory.id == filters.category_id)
            )
        elif filters.uncategorized_only:
            statement = statement.where(~Product.categories.any())

        search_text = (filters.search_text or "").strip().lower()
        if search_text:
            search_pattern = f"%{ListProductsService._escape_like(search_text)}%"
            statement = statement.where(
                or_(
                    func.lower(Product.name).like(search_pattern, escape="\\"),
                    func.lower(Product.description).like(search_pattern, escape="\\"),
                    Product.supplier.has(
                        func.lower(Supplier.name).like(search_pattern, escape="\\")
                    ),
                    Product.categories.any(
                        func.lower(ProductCategory.name).like(search_pattern, escape="\\")
                    ),
                    Product.variants.any(
                        func.lower(ProductVariant.sku).like(search_pattern, escape="\\")
                    ),
                    Product.variants.any(
                        func.lower(ProductVariant.variant_name).like(
                            search_pattern,
                            escape="\\",
                        )
                    ),
                    Product.variants.any(
                        func.lower(ProductVariant.size).like(search_pattern, escape="\\")
                    ),
                    Product.variants.any(
                        func.lower(ProductVariant.color).like(search_pattern, escape="\\")
                    ),
                )
            )

        return statement

    @staticmethod
    def _escape_like(value: str) -> str:
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    @staticmethod
    def _category_summaries(product: Product) -> list[ProductCategorySummary]:
        return [
            ProductCategorySummary(
                id=category.id,
                name=category.name,
                is_active=category.is_active,
            )
            for category in product.categories
        ]


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


class ListProductVariantPickerOptionsService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self) -> list[ProductVariantPickerItem]:
        statement = (
            select(ProductVariant)
            .join(ProductVariant.product)
            .options(joinedload(ProductVariant.product).selectinload(Product.categories))
            .order_by(Product.name, ProductVariant.id)
        )
        variants = self._session.scalars(statement).all()

        return [
            ProductVariantPickerItem(
                id=variant.id,
                product_id=variant.product_id,
                product_name=variant.product.name,
                sku=variant.sku,
                size=variant.size,
                color=variant.color,
                variant_name=variant.variant_name,
                price=(
                    variant.price_override
                    if variant.price_override is not None
                    else variant.product.base_price
                ),
                product_is_active=variant.product.is_active,
                variant_is_active=variant.is_active,
                category_names=[
                    category.name
                    for category in variant.product.categories
                ],
            )
            for variant in variants
        ]


class GetProductForEditService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, product_id: int) -> ProductEditItem:
        product = self._session.get(
            Product,
            product_id,
            options=[
                joinedload(Product.supplier),
                selectinload(Product.variants),
                selectinload(Product.categories),
            ],
        )

        if product is None:
            raise ValueError("Product not found.")

        default_variant = self._default_variant(product)
        variants = [
            ProductVariantEditItem(
                id=variant.id,
                sku=variant.sku,
                size=variant.size,
                color=variant.color,
                variant_name=variant.variant_name,
                description=variant.description,
                price_override=variant.price_override,
                stock_current=variant.stock_current,
                stock_minimum=variant.stock_minimum,
                is_active=variant.is_active,
            )
            for variant in sorted(product.variants, key=lambda item: item.id)
        ]

        return ProductEditItem(
            id=product.id,
            supplier_id=product.supplier_id,
            supplier_name=product.supplier.name if product.supplier else None,
            name=product.name,
            description=product.description,
            base_price=product.base_price,
            track_stock=product.track_stock,
            is_active=product.is_active,
            categories=ListProductsService._category_summaries(product),
            default_variant=ProductVariantEditItem(
                id=default_variant.id,
                sku=default_variant.sku,
                size=default_variant.size,
                color=default_variant.color,
                variant_name=default_variant.variant_name,
                description=default_variant.description,
                price_override=default_variant.price_override,
                stock_current=default_variant.stock_current,
                stock_minimum=default_variant.stock_minimum,
                is_active=default_variant.is_active,
            ),
            variants=variants,
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
            options=[selectinload(Product.variants), selectinload(Product.categories)],
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

        if data.category_ids is not UNSET:
            self._validate_unique_category_ids(data.category_ids)
            existing_category_ids = {category.id for category in product.categories}
            product.categories = self._load_categories(
                data.category_ids,
                allow_inactive_category_ids=existing_category_ids,
            )

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

            if data.default_variant.stock_current is not UNSET:
                variant.stock_current = data.default_variant.stock_current

            if data.default_variant.stock_minimum is not UNSET:
                variant.stock_minimum = data.default_variant.stock_minimum

        self._session.flush()
        if data.category_ids is not UNSET:
            CreateProductService(self._session)._set_category_order(product.id, data.category_ids)

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

        if data.category_ids is not UNSET:
            self._validate_unique_category_ids(data.category_ids)

    def _validate_variant_input(self, variant: UpdateProductVariantInput) -> None:
        if variant.price_override is not UNSET:
            CreateProductService._validate_decimal_amount(
                variant.price_override,
                "Default variant price override must be a finite number.",
                "Default variant price override cannot be negative.",
            )

        if variant.stock_current is not UNSET and variant.stock_current is not None:
            if variant.stock_current < 0:
                raise ValueError("Default variant stock_current cannot be negative.")

        if variant.stock_minimum is not UNSET and variant.stock_minimum is not None:
            if variant.stock_minimum < 0:
                raise ValueError("Default variant stock_minimum cannot be negative.")

    @staticmethod
    def _validate_unique_category_ids(category_ids: list[int]) -> None:
        if len(category_ids) != len(set(category_ids)):
            raise ValueError("Product categories must be unique.")

    @staticmethod
    def _find_product_variant(product: Product, variant_id: int) -> ProductVariant:
        for variant in product.variants:
            if variant.id == variant_id:
                return variant

        raise ValueError("Product variant not found.")

    def _load_categories(
        self,
        category_ids: list[int],
        allow_inactive_category_ids: set[int] | None = None,
    ) -> list[ProductCategory]:
        return CreateProductService(self._session)._load_categories(
            category_ids,
            allow_inactive_category_ids=allow_inactive_category_ids,
        )


class ProductStatusService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(
        self,
        product_id: int,
        is_active: bool,
        active_variant_ids: list[int] | tuple[int, ...] | None = None,
    ) -> Product:
        product = self._session.get(
            Product,
            product_id,
            options=[selectinload(Product.variants)],
        )

        if product is None:
            raise ValueError("Product not found.")

        if product.is_active == is_active:
            status = "active" if is_active else "inactive"
            raise ValueError(f"Product is already {status}.")

        if is_active:
            if active_variant_ids is not None:
                self._activate_selected_variants(product, active_variant_ids)
            if not any(variant.is_active for variant in product.variants):
                raise ValueError("Product must have at least one active variant to be active.")

        product.is_active = is_active
        if not is_active:
            for variant in product.variants:
                variant.is_active = False
        self._session.flush()

        return product

    @staticmethod
    def _activate_selected_variants(
        product: Product,
        active_variant_ids: list[int] | tuple[int, ...],
    ) -> None:
        selected_variant_ids = set(active_variant_ids)
        product_variant_ids = {variant.id for variant in product.variants}
        if not selected_variant_ids:
            raise ValueError("Select at least one product variant to activate.")
        if not selected_variant_ids <= product_variant_ids:
            raise ValueError("Product variant not found.")

        for variant in product.variants:
            variant.is_active = variant.id in selected_variant_ids


class CreateProductVariantService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, product_id: int, data: CreateProductVariantInput) -> ProductVariant:
        product = self._session.get(
            Product,
            product_id,
            options=[selectinload(Product.variants)],
        )

        if product is None:
            raise ValueError("Product not found.")

        variant_index = self._next_variant_index(product.id)
        create_service = CreateProductService(self._session)
        create_service._validate_variant_input(data, variant_index)

        sku = create_service._normalize_sku(data.sku) or create_service._generate_sku(
            product.name,
            product.id,
            variant_index,
        )
        self._validate_unique_sku(sku)

        variant = ProductVariant(
            product_id=product.id,
            sku=sku,
            size=data.size,
            color=data.color,
            variant_name=data.variant_name,
            description=data.description,
            price_override=data.price_override,
            stock_current=data.stock_current,
            stock_minimum=data.stock_minimum,
            is_active=data.is_active,
        )

        self._session.add(variant)
        self._session.flush()

        return variant

    def _validate_unique_sku(self, sku: str) -> None:
        existing_variant = self._session.scalar(
            select(ProductVariant).where(ProductVariant.sku == sku)
        )
        if existing_variant is not None:
            raise ValueError("Product variant SKU already exists.")

    def _next_variant_index(self, product_id: int) -> int:
        variant_count = self._session.scalar(
            select(func.count()).select_from(ProductVariant).where(
                ProductVariant.product_id == product_id
            )
        )
        return (variant_count or 0) + 1


class UpdateProductVariantService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, variant_id: int, data: UpdateProductVariantInput) -> ProductVariant:
        self._validate_variant_input(data, "Product variant")

        variant = self._session.get(ProductVariant, variant_id)

        if variant is None:
            raise ValueError("Product variant not found.")

        if data.size is not UNSET:
            variant.size = data.size

        if data.color is not UNSET:
            variant.color = data.color

        if data.variant_name is not UNSET:
            variant.variant_name = data.variant_name

        if data.description is not UNSET:
            variant.description = data.description

        if data.price_override is not UNSET:
            variant.price_override = data.price_override

        if data.stock_current is not UNSET:
            variant.stock_current = data.stock_current

        if data.stock_minimum is not UNSET:
            variant.stock_minimum = data.stock_minimum

        self._session.flush()

        return variant

    @staticmethod
    def _validate_variant_input(data: UpdateProductVariantInput, label: str) -> None:
        if data.price_override is not UNSET:
            CreateProductService._validate_decimal_amount(
                data.price_override,
                f"{label} price override must be a finite number.",
                f"{label} price override cannot be negative.",
            )

        if data.stock_current is not UNSET and data.stock_current is not None:
            if data.stock_current < 0:
                raise ValueError(f"{label} stock_current cannot be negative.")

        if data.stock_minimum is not UNSET and data.stock_minimum is not None:
            if data.stock_minimum < 0:
                raise ValueError(f"{label} stock_minimum cannot be negative.")


class ProductVariantStatusService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, variant_id: int, is_active: bool) -> ProductVariant:
        variant = self._session.get(
            ProductVariant,
            variant_id,
            options=[joinedload(ProductVariant.product).selectinload(Product.variants)],
        )

        if variant is None:
            raise ValueError("Product variant not found.")

        if variant.is_active == is_active:
            status = "active" if is_active else "inactive"
            raise ValueError(f"Product variant is already {status}.")

        variant.is_active = is_active

        if not is_active and not any(item.is_active for item in variant.product.variants):
            variant.product.is_active = False

        self._session.flush()

        return variant
