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
        "Dashboard": "Panel",
        "Shortcuts": "Accesos directos",
        "Quick Actions": "Acciones rápidas",
        "Daily Tasks": "Tareas del día",
        "Overdue": "Atrasadas",
        "Pending Today": "Pendientes hoy",
        "Completed Today": "Completadas hoy",
        "No overdue tasks.": "No hay tareas atrasadas.",
        "No pending tasks for today.": "No hay tareas pendientes para hoy.",
        "No completed tasks for today.": "No hay tareas completadas para hoy.",
        "New Task": "Nueva tarea",
        "Create Task": "Crear tarea",
        "Title": "Título",
        "Due date": "Fecha de vencimiento",
        "Complete": "Completar",
        "Reopen": "Reabrir",
        "Could not create task": "No se pudo crear la tarea",
        "Could not load tasks": "No se pudieron cargar las tareas",
        "Could not update task": "No se pudo actualizar la tarea",
        "Task title is required.": "El título de la tarea es obligatorio.",
        "Task not found.": "No se encontró la tarea.",
        "Task series title is required.": "El título de la serie de tareas es obligatorio.",
        "Task recurrence interval must be at least 1.": (
            "El intervalo de repetición de la tarea debe ser al menos 1."
        ),
        "Task series end date cannot be before the start date.": (
            "La fecha de fin de la serie de tareas no puede ser anterior a la fecha de inicio."
        ),
        "Task generation horizon days must be between 30 and 365.": (
            "Los días del horizonte de generación de tareas deben estar entre 30 y 365."
        ),
        "Products": "Productos",
        "Categories": "Categorías",
        "Product Categories": "Categorías de producto",
        "Suppliers": "Proveedores",
        "Customers": "Clientes",
        "Orders": "Pedidos",
        "Settings": "Ajustes",
        "New Product": "Nuevo producto",
        "Edit Product": "Editar producto",
        "New Category": "Nueva categoría",
        "Edit Category": "Editar categoría",
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
        "Recover Order": "Recuperar pedido",
        "Refresh": "Actualizar",
        "ID": "ID",
        "Name": "Nombre",
        "Supplier": "Proveedor",
        "Base Price": "Precio base",
        "Track Stock": "Controlar stock",
        "Status": "Estado",
        "Variant Summary": "Resumen de variantes",
        "Category": "Categoría",
        "Selected": "Seleccionado",
        "Selected Categories": "Categorías seleccionadas",
        "Available Categories": "Categorías disponibles",
        "Add Category": "Añadir categoría",
        "No categories selected": "Sin categorías seleccionadas",
        "All Categories": "Todas las categorías",
        "Uncategorized": "Sin categoría",
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
        "Variants": "Variantes",
        "Product Details": "Detalles del producto",
        "SKU": "SKU",
        "Manual SKU": "SKU manual",
        "Size": "Talla",
        "Color": "Color",
        "Price": "Precio",
        "Product Variant": "Variante de producto",
        "Product variant": "Variante de producto",
        "Add Variant": "Añadir variante",
        "Edit Variant": "Editar variante",
        "Activate Variant": "Activar variante",
        "Deactivate Variant": "Desactivar variante",
        "Deactivate variant": "Desactivar variante",
        "This is the last active variant. The product will become inactive. Continue?": (
            "Esta es la última variante activa. El producto quedará inactivo. ¿Continuar?"
        ),
        "Price override": "Precio específico",
        "Current stock": "Stock actual",
        "Minimum stock": "Stock mínimo",
        "Add at least one product variant.": "Añade al menos una variante de producto.",
        "Product name is required.": "El nombre del producto es obligatorio.",
        "A product must have at least one variant.": "Un producto debe tener al menos una variante.",
        "Product must have at least one active variant to be active.": (
            "El producto debe tener al menos una variante activa para estar activo."
        ),
        "Select at least one product variant to activate.": (
            "Selecciona al menos una variante de producto para activar."
        ),
        "Product variant SKU already exists.": "El SKU de la variante de producto ya existe.",
        "Product variant SKU cannot be blank.": "El SKU de la variante de producto no puede estar vacío.",
        "Product variant not found.": "No se encontró la variante de producto.",
        "Product variant is already active.": "La variante de producto ya está activa.",
        "Product variant is already inactive.": "La variante de producto ya está inactiva.",
        "Activate product variants": "Activar variantes del producto",
        "Select All": "Seleccionar todo",
        "Deselect All": "Deseleccionar todo",
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
        "Create Category": "Crear categoría",
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
        "No category selected": "Ninguna categoría seleccionada",
        "Select a category to edit.": "Selecciona una categoría para editar.",
        "Could not load category": "No se pudo cargar la categoría",
        "Could not save category": "No se pudo guardar la categoría",
        "Could not load categories": "No se pudieron cargar las categorías",
        "Product category name is required.": "El nombre de la categoría es obligatorio.",
        "Product category name already exists.": "El nombre de la categoría ya existe.",
        "Product category not found.": "No se encontró la categoría de producto.",
        "Product category must be active.": "La categoría de producto debe estar activa.",
        "Product categories must be unique.": "Las categorías del producto deben ser únicas.",
        "Could not create product variant": "No se pudo crear la variante de producto",
        "Could not update product variant": "No se pudo actualizar la variante de producto",
        "Could not load product variants": "No se pudieron cargar las variantes de producto",
        "Invalid data": "Datos no válidos",
        "Product was not loaded.": "El producto no se cargó.",
        "{field_label} must be a valid number.": "{field_label} debe ser un número válido.",
        "{field_label} must be a finite number.": "{field_label} debe ser un número finito.",
        "Search by name, tax ID, phone, or email": ("Buscar por nombre, NIF/CIF, teléfono o email"),
        "Search by name, company, tax ID, phone, or email": (
            "Buscar por nombre, empresa, NIF/CIF, teléfono o email"
        ),
        "Search by product, category, SKU, variant, size, or color": (
            "Buscar por producto, categoría, SKU, variante, talla o color"
        ),
        "Search by product, category, supplier, SKU, variant, size, or color": (
            "Buscar por producto, categoría, proveedor, SKU, variante, talla o color"
        ),
        "No order selected": "Ningún pedido seleccionado",
        "Select an active order to edit.": "Selecciona un pedido activo para editar.",
        "Could not check order edit policy": "No se pudo comprobar la política de edición",
        "Order cannot be edited": "El pedido no se puede editar",
        "Select an order to advance.": "Selecciona un pedido para avanzar.",
        "Order cannot advance": "El pedido no puede avanzar",
        "This order cannot be advanced in the configured workflow.": (
            "Este pedido no puede avanzar en el flujo configurado."
        ),
        "Select an order to revert.": "Selecciona un pedido para revertir.",
        "Order cannot revert": "El pedido no puede revertirse",
        "This order cannot be reverted in the configured workflow.": (
            "Este pedido no puede revertirse en el flujo configurado."
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
        "Select an order to recover.": "Selecciona un pedido para recuperar.",
        "Order cannot be recovered": "El pedido no se puede recuperar",
        "Only cancelled orders can be recovered to draft.": (
            "Solo los pedidos cancelados se pueden recuperar como borrador."
        ),
        "Recover order": "Recuperar pedido",
        "Recover this cancelled order to draft?": (
            "¿Recuperar este pedido cancelado como borrador?"
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
        "This order status cannot be edited.": "Este estado del pedido no se puede editar.",
        "Ready orders only allow deadline, discount, and notes changes.": (
            "Los pedidos listos solo permiten cambiar la fecha límite, el descuento y las notas."
        ),
        "Completed and cancelled orders only allow notes changes.": (
            "Los pedidos completados y cancelados solo permiten cambiar las notas."
        ),
        "Language": "Idioma",
        "English": "Inglés",
        "Spanish": "Español",
        "Strict order workflow": "Flujo estricto de pedidos",
        "Task generation horizon": "Horizonte de generación de tareas",
        "days": "días",
        "Recurring task occurrences are generated this many days ahead.": (
            "Las ocurrencias de tareas recurrentes se generan con esta cantidad de días "
            "de antelación."
        ),
        "Enabled order statuses": "Estados de pedido habilitados",
        "Choose which statuses are used when advancing or reverting orders. Draft, completed, and cancelled are always required.": (
            "Elige qué estados se usan al avanzar o revertir pedidos. Borrador, completado "
            "y cancelado siempre son obligatorios."
        ),
        "Disable order statuses": "Desactivar estados de pedido",
        "Orders currently in disabled statuses will be converted to draft:": (
            "Los pedidos que estén en estados desactivados se convertirán a borrador:"
        ),
        "Continue saving settings?": "¿Continuar guardando los ajustes?",
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
