# src/api/schemas/tiendanube.py
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel

# === Nested models (de adentro hacia afuera) ===


class InventoryLevel(BaseModel):
    id: int
    variant_id: int
    location_id: str
    stock: int | None = None


class VariantValue(BaseModel):
    es: str


class Variant(BaseModel):
    id: int
    image_id: Optional[int] = None
    product_id: int
    position: int
    price: Decimal  # TiendaNube devuelve como string
    compare_at_price: Optional[Decimal] = None
    promotional_price: Optional[Decimal] = None
    stock_management: bool
    stock: int | None = None
    weight: Optional[Decimal] = None
    width: Optional[Decimal] = None
    height: Optional[Decimal] = None
    depth: Optional[Decimal] = None
    sku: Optional[str] = None
    values: list[VariantValue]
    barcode: Optional[str] = None
    mpn: Optional[str] = None
    age_group: Optional[str] = None
    gender: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    cost: Optional[Decimal] = None
    visible: bool = True
    inventory_levels: list[InventoryLevel] = []


class TiendaNubeVariantDB(BaseModel):
    tiendanube_variant_id: int  # API: id
    product_id: int  # API: product_id (FK a tiendanube_product.tiendanube_id)
    tenant_id: int
    values: list[str]
    price: Decimal
    promotional_price: Optional[Decimal] = None
    cost: Optional[Decimal] = None
    sku: Optional[str] = None
    stock: int
    stock_management: bool = True
    weight: Optional[Decimal] = None
    width: Optional[Decimal] = None
    height: Optional[Decimal] = None
    depth: Optional[Decimal] = None
    tn_created_at: datetime
    tn_updated_at: datetime

    @classmethod
    def from_tiendanube_variant(
        cls, variant: Variant, tenant_id: int
    ) -> "TiendaNubeVariantDB":
        return cls(
            tiendanube_variant_id=variant.id,
            product_id=variant.product_id,
            tenant_id=tenant_id,
            values=[val.es for val in variant.values if val.es],
            price=Decimal(variant.price),
            promotional_price=Decimal(variant.promotional_price)
            if variant.promotional_price
            else None,
            cost=Decimal(variant.cost) if variant.cost else None,
            sku=variant.sku if variant.sku and variant.sku.strip() else None,
            stock=variant.stock if variant.stock else 0,
            stock_management=variant.stock_management,
            weight=Decimal(variant.weight) if variant.weight else None,
            width=Decimal(variant.width) if variant.width else None,
            height=Decimal(variant.height) if variant.height else None,
            depth=Decimal(variant.depth) if variant.depth else None,
            tn_created_at=variant.created_at,
            tn_updated_at=variant.updated_at,
        )


class Image(BaseModel):
    id: int
    product_id: int
    src: str
    position: int
    alt: list[Any] = []
    height: int
    width: int
    thumbnails_generated: int
    created_at: datetime
    updated_at: datetime


class LocalizedText(BaseModel):
    es: Optional[str] = None


class NotOptLocalizedText(BaseModel):
    es: str


class Category(BaseModel):
    id: int
    name: LocalizedText
    description: LocalizedText
    handle: LocalizedText
    parent: Optional[int] = None
    subcategories: list[int] = []
    # seo_title: LocalizedText
    # seo_description: LocalizedText
    google_shopping_category: str = ""
    created_at: datetime
    updated_at: datetime


# === Main Product model ===


class TiendaNubeProduct(BaseModel):
    id: int
    name: NotOptLocalizedText
    description: Optional[LocalizedText] = None
    handle: Optional[LocalizedText] = None
    attributes: list[LocalizedText] = []
    published: bool = True
    free_shipping: bool = False
    requires_shipping: bool = True
    canonical_url: Optional[str] = None
    # video_url: Optional[str] = None
    # seo_title: Optional[LocalizedText] = None
    # seo_description: Optional[LocalizedText] = None
    brand: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Nested objects
    variants: list[Variant]
    images: list[Image] = []
    categories: list[Category] = []

    # list for SQL optimization
    tags: str | None = None


class TiendaNubeProductDB(BaseModel):
    tiendanube_id: int
    tenant_id: int
    name: str
    description: Optional[str] = None
    handle: Optional[str] = None
    attributes: list[str] = []
    published: bool = True
    free_shipping: bool = False
    requires_shipping: bool = True
    canonical_url: Optional[str] = None
    brand: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Nested objects
    variants: list[str] = []
    images_url: list[str] = []
    category_ids: list[int] = []

    # list for SQL optimization
    tags: list[str] = []

    @classmethod
    def from_tiendanube_response(
        cls, tn_product: TiendaNubeProduct, tenant_id: int
    ) -> "TiendaNubeProductDB":
        return cls(
            tiendanube_id=tn_product.id,
            tenant_id=tenant_id,
            name=tn_product.name.es,
            description=tn_product.description.es if tn_product.description else None,
            handle=tn_product.handle.es if tn_product.handle else None,
            attributes=[
                attr.es
                for attr in tn_product.attributes
                if attr.es  # ← Filtrar None y strings vacíos
            ]
            if tn_product.attributes
            else [],
            published=tn_product.published,
            free_shipping=tn_product.free_shipping,
            requires_shipping=tn_product.requires_shipping,
            canonical_url=tn_product.canonical_url,
            brand=tn_product.brand,
            created_at=tn_product.created_at,
            updated_at=tn_product.updated_at,
            images_url=[img.src for img in tn_product.images]
            if tn_product.images
            else [],
            category_ids=[cat.id for cat in tn_product.categories]
            if tn_product.categories
            else [],
            tags=tn_product.tags.split(",") if tn_product.tags else [],
        )
