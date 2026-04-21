from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.application.dto.product_categories import (
    CreateProductCategoryInput,
    ProductCategoryEditItem,
    ProductCategoryListItem,
    ProductCategoryOption,
    UpdateProductCategoryInput,
)
from app.infrastructure.db.models import ProductCategory


class CreateProductCategoryService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, data: CreateProductCategoryInput) -> ProductCategory:
        self._validate_category_input(data)
        self._validate_unique_name(data.name)

        category = ProductCategory(
            name=data.name.strip(),
            description=data.description,
            is_active=data.is_active,
        )

        self._session.add(category)
        self._session.flush()

        return category

    def _validate_unique_name(self, name: str, category_id: int | None = None) -> None:
        statement = select(ProductCategory).where(
            func.lower(ProductCategory.name) == name.strip().lower()
        )
        if category_id is not None:
            statement = statement.where(ProductCategory.id != category_id)

        existing = self._session.scalar(statement)
        if existing is not None:
            raise ValueError("Product category name already exists.")

    @staticmethod
    def _validate_category_input(
        data: CreateProductCategoryInput | UpdateProductCategoryInput,
    ) -> None:
        if not data.name or not data.name.strip():
            raise ValueError("Product category name is required.")


class UpdateProductCategoryService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, category_id: int, data: UpdateProductCategoryInput) -> ProductCategory:
        CreateProductCategoryService._validate_category_input(data)
        CreateProductCategoryService(self._session)._validate_unique_name(data.name, category_id)

        category = self._session.get(ProductCategory, category_id)

        if category is None:
            raise ValueError("Product category not found.")

        category.name = data.name.strip()
        category.description = data.description
        category.is_active = data.is_active

        self._session.flush()

        return category


class ListProductCategoriesService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self) -> list[ProductCategoryListItem]:
        categories = self._session.scalars(
            select(ProductCategory).order_by(ProductCategory.name, ProductCategory.id)
        ).all()

        return [
            ProductCategoryListItem(
                id=category.id,
                name=category.name,
                description=category.description,
                is_active=category.is_active,
            )
            for category in categories
        ]


class GetProductCategoryForEditService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self, category_id: int) -> ProductCategoryEditItem:
        category = self._session.get(ProductCategory, category_id)

        if category is None:
            raise ValueError("Product category not found.")

        return ProductCategoryEditItem(
            id=category.id,
            name=category.name,
            description=category.description,
            is_active=category.is_active,
        )


class ListProductCategoryOptionsService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def execute(self) -> list[ProductCategoryOption]:
        categories = self._session.scalars(
            select(ProductCategory).order_by(ProductCategory.name, ProductCategory.id)
        ).all()

        return [
            ProductCategoryOption(
                id=category.id,
                name=category.name,
                description=category.description,
                is_active=category.is_active,
            )
            for category in categories
        ]
