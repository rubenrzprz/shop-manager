from app.domain.enums import OrderStatus

DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = {"en": "English", "es": "Español"}

_current_language = DEFAULT_LANGUAGE


def set_language(language: str) -> None:
    global _current_language
    _current_language = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def current_language() -> str:
    return _current_language


def t(text: str) -> str:
    if _current_language == DEFAULT_LANGUAGE:
        return text

    return _TRANSLATIONS.get(_current_language, {}).get(text, text)


def order_status_label(status: OrderStatus) -> str:
    return t(status.value.title().replace("_", " "))


_TRANSLATIONS = {
    "es": {
        "Shop Manager": "Gestor de tienda",
        "Products": "Productos",
        "Suppliers": "Proveedores",
        "Customers": "Clientes",
        "Orders": "Pedidos",
        "Settings": "Ajustes",
        "New Product": "Nuevo producto",
        "Edit Product": "Editar producto",
        "Activate Product": "Activar producto",
        "Deactivate Product": "Desactivar producto",
        "New Supplier": "Nuevo proveedor",
        "Edit Supplier": "Editar proveedor",
        "New Customer": "Nuevo cliente",
        "Edit Customer": "Editar cliente",
        "New Order": "Nuevo pedido",
        "Edit Order": "Editar pedido",
        "Advance Status": "Avanzar estado",
        "Revert Status": "Revertir estado",
        "Cancel Order": "Cancelar pedido",
        "Refresh": "Actualizar",
        "ID": "ID",
        "Name": "Nombre",
        "Supplier": "Proveedor",
        "Base Price": "Precio base",
        "Track Stock": "Controlar stock",
        "Status": "Estado",
        "Variant Summary": "Resumen de variantes",
        "Tax ID": "NIF/CIF",
        "Phone": "Teléfono",
        "Email": "Email",
        "City": "Ciudad",
        "Country": "País",
        "Type": "Tipo",
        "Company": "Empresa",
        "Company name": "Nombre de la empresa",
        "Order #": "Pedido #",
        "Customer": "Cliente",
        "Order Date": "Fecha del pedido",
        "Order date": "Fecha del pedido",
        "Deadline": "Fecha límite",
        "Lines": "Líneas",
        "Total": "Total",
        "Description": "Descripción",
        "Base price": "Precio base",
        "Default variant name": "Nombre de variante predeterminada",
        "Default variant size": "Talla de variante predeterminada",
        "Default variant color": "Color de variante predeterminada",
        "Default variant price override": "Precio específico de variante predeterminada",
        "Default variant description": "Descripción de variante predeterminada",
        "Address line 1": "Dirección 1",
        "Address line 2": "Dirección 2",
        "Postal code": "Código postal",
        "Notes": "Notas",
        "Product": "Producto",
        "Variant": "Variante",
        "Size": "Talla",
        "Color": "Color",
        "Price": "Precio",
        "Product Variant": "Variante de producto",
        "Product variant": "Variante de producto",
        "Qty": "Cant.",
        "Unit Price": "Precio unitario",
        "Unit price": "Precio unitario",
        "Line Total": "Total línea",
        "Quantity": "Cantidad",
        "Subtotal": "Subtotal",
        "Discount": "Descuento",
        "Discount type": "Tipo de descuento",
        "Discount value": "Valor del descuento",
        "Total preview": "Vista previa del total",
        "Add line": "Añadir línea",
        "Add Line": "Añadir línea",
        "None": "Ninguno",
        "Fixed": "Fijo",
        "Percentage": "Porcentaje",
        "Remove": "Eliminar",
        "Clear": "Limpiar",
        "Select": "Seleccionar",
        "Select Supplier": "Seleccionar proveedor",
        "Select Customer": "Seleccionar cliente",
        "Select Variant": "Seleccionar variante",
        "Select Product Variant": "Seleccionar variante de producto",
        "Create Product": "Crear producto",
        "Create Supplier": "Crear proveedor",
        "Create Customer": "Crear cliente",
        "Create Order": "Crear pedido",
        "Active": "Activo",
        "Inactive": "Inactivo",
        "Individual": "Particular",
        "No": "No",
        "Yes": "Sí",
        "Save": "Guardar",
        "Cancel": "Cancelar",
        "OK": "Aceptar",
        "No variants": "Sin variantes",
        "Default": "Predeterminada",
        "Draft": "Borrador",
        "Confirmed": "Confirmado",
        "In Progress": "En curso",
        "Ready": "Listo",
        "Completed": "Completado",
        "Cancelled": "Cancelado",
        "No product selected": "Ningún producto seleccionado",
        "Select a product to edit.": "Selecciona un producto para editar.",
        "Select a product to activate.": "Selecciona un producto para activar.",
        "Select a product to deactivate.": "Selecciona un producto para desactivar.",
        "Product already active": "El producto ya está activo",
        "Product already inactive": "El producto ya está inactivo",
        "The selected product is already active.": "El producto seleccionado ya está activo.",
        "The selected product is already inactive.": "El producto seleccionado ya está inactivo.",
        "Activate product": "Activar producto",
        "Deactivate product": "Desactivar producto",
        "Activate the selected product?": "¿Activar el producto seleccionado?",
        "Deactivate the selected product?": "¿Desactivar el producto seleccionado?",
        "Could not activate product": "No se pudo activar el producto",
        "Could not deactivate product": "No se pudo desactivar el producto",
        "Could not load products": "No se pudieron cargar los productos",
        "No supplier selected": "Ningún proveedor seleccionado",
        "Select a supplier.": "Selecciona un proveedor.",
        "Select a supplier to edit.": "Selecciona un proveedor para editar.",
        "Could not load supplier": "No se pudo cargar el proveedor",
        "Could not save supplier": "No se pudo guardar el proveedor",
        "Could not load suppliers": "No se pudieron cargar los proveedores",
        "No customer selected": "Ningún cliente seleccionado",
        "Select a customer.": "Selecciona un cliente.",
        "Select a customer to edit.": "Selecciona un cliente para editar.",
        "Inactive customer": "Cliente inactivo",
        "Select an active customer.": "Selecciona un cliente activo.",
        "Could not load customer": "No se pudo cargar el cliente",
        "Could not save customer": "No se pudo guardar el cliente",
        "Could not load customers": "No se pudieron cargar los clientes",
        "No product variant selected": "Ninguna variante de producto seleccionada",
        "Select a product variant.": "Selecciona una variante de producto.",
        "Inactive product variant": "Variante de producto inactiva",
        "Select an active product variant from an active product.": (
            "Selecciona una variante activa de un producto activo."
        ),
        "Could not load product": "No se pudo cargar el producto",
        "Could not create product": "No se pudo crear el producto",
        "Could not update product": "No se pudo actualizar el producto",
        "Could not load product variants": "No se pudieron cargar las variantes de producto",
        "Invalid data": "Datos no válidos",
        "Product was not loaded.": "El producto no se cargó.",
        "{field_label} must be a valid number.": "{field_label} debe ser un número válido.",
        "{field_label} must be a finite number.": "{field_label} debe ser un número finito.",
        "Search by name, tax ID, phone, or email": ("Buscar por nombre, NIF/CIF, teléfono o email"),
        "Search by name, company, tax ID, phone, or email": (
            "Buscar por nombre, empresa, NIF/CIF, teléfono o email"
        ),
        "Search by product, SKU, variant, size, or color": (
            "Buscar por producto, SKU, variante, talla o color"
        ),
        "No order selected": "Ningún pedido seleccionado",
        "Select an active order to edit.": "Selecciona un pedido activo para editar.",
        "Could not check order edit policy": "No se pudo comprobar la política de edición",
        "Order cannot be edited": "El pedido no se puede editar",
        "Select an order to advance.": "Selecciona un pedido para avanzar.",
        "Order cannot advance": "El pedido no puede avanzar",
        "Completed and cancelled orders cannot be advanced.": (
            "Los pedidos completados y cancelados no pueden avanzar."
        ),
        "Select an order to revert.": "Selecciona un pedido para revertir.",
        "Order cannot revert": "El pedido no puede revertirse",
        "Draft and cancelled orders cannot be reverted.": (
            "Los pedidos en borrador y cancelados no pueden revertirse."
        ),
        "Select an order to cancel.": "Selecciona un pedido para cancelar.",
        "Order cannot be cancelled": "El pedido no puede cancelarse",
        "Completed and cancelled orders cannot be cancelled.": (
            "Los pedidos completados y cancelados no pueden cancelarse."
        ),
        "Cancel order": "Cancelar pedido",
        "Cancel this order? This cannot be undone from the current workflow.": (
            "¿Cancelar este pedido? Esto no se puede deshacer con el flujo actual."
        ),
        "Could not update order status": "No se pudo actualizar el estado del pedido",
        "Could not load orders": "No se pudieron cargar los pedidos",
        "Set deadline": "Definir fecha límite",
        "Enter price": "Introduce precio",
        "Missing product variant": "Falta variante de producto",
        "Missing customer": "Falta cliente",
        "Missing order data": "Faltan datos del pedido",
        "Add at least one order line.": "Añade al menos una línea al pedido.",
        "Could not load order": "No se pudo cargar el pedido",
        "Could not save order": "No se pudo guardar el pedido",
        "Strict order workflow is enabled. Only draft orders can be fully edited.": (
            "El flujo estricto de pedidos está activado. Solo los pedidos en borrador "
            "se pueden editar por completo."
        ),
        "Only active orders can be edited.": "Solo se pueden editar pedidos activos.",
        "Language": "Idioma",
        "English": "Inglés",
        "Spanish": "Español",
        "Strict order workflow": "Flujo estricto de pedidos",
        "When enabled, only draft orders can be fully edited. When disabled, active orders can be edited with the same rules as drafts.": (
            "Cuando está activado, solo los pedidos en borrador se pueden editar por completo. "
            "Cuando está desactivado, los pedidos activos se pueden editar con las mismas "
            "reglas que los borradores."
        ),
        "Save Settings": "Guardar ajustes",
        "Could not load settings": "No se pudieron cargar los ajustes",
        "Could not save settings": "No se pudieron guardar los ajustes",
        "Settings saved": "Ajustes guardados",
        "Settings saved.": "Ajustes guardados.",
    }
}
