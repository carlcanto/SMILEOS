<script setup>
import { computed, onMounted, ref } from 'vue'
import { useQuasar } from 'quasar'

const STORAGE_KEY = 'smileos-inventory-v1'
const MOVEMENTS_KEY = 'smileos-inventory-movements-v1'
const $q = useQuasar()

const categories = ['Material odontológico', 'Bioseguridad', 'Instrumental', 'Medicamentos', 'Limpieza', 'Oficina', 'Otro']
const units = ['unidad', 'caja', 'paquete', 'frasco', 'litro', 'par', 'rollo', 'kit']
const categoryOptions = categories
const searchQuery = ref('')
const selectedCategory = ref('')
const stockFilter = ref('todos')
const activeTab = ref('products')
const productDialog = ref(false)
const movementDialog = ref(false)
const editingId = ref(null)
const movementProduct = ref(null)
const productForm = ref(emptyProduct())
const movementForm = ref(emptyMovement())

function emptyProduct() {
  return {
    sku: '', name: '', category: '', unit: 'unidad', quantity: 0, minimum: 1,
    supplier: '', lot: '', expirationDate: '', unitCost: 0, location: '', notes: '',
  }
}

function emptyMovement() {
  return { type: 'entrada', quantity: 1, date: new Date().toISOString().slice(0, 10), reference: '', notes: '' }
}

const products = ref([])
const movements = ref([])

const seedProducts = [
  { id: 'inv-001', sku: 'MAT-001', name: 'Guantes de nitrilo', category: 'Bioseguridad', unit: 'caja', quantity: 18, minimum: 6, supplier: 'Dental Supply Panamá', lot: 'GN-2408', expirationDate: '2027-08-31', unitCost: 8.5, location: 'Almacén A · Estante 1', notes: '' },
  { id: 'inv-002', sku: 'MAT-002', name: 'Mascarillas quirúrgicas', category: 'Bioseguridad', unit: 'caja', quantity: 4, minimum: 6, supplier: 'Dental Supply Panamá', lot: 'MQ-2510', expirationDate: '2028-02-28', unitCost: 5.25, location: 'Almacén A · Estante 1', notes: '' },
  { id: 'inv-003', sku: 'ODO-001', name: 'Resina compuesta A2', category: 'Material odontológico', unit: 'jeringa', quantity: 12, minimum: 4, supplier: 'Depósito Dental Central', lot: 'RC-A2-119', expirationDate: '2026-12-15', unitCost: 18.75, location: 'Gabinete clínico · Nivel 2', notes: '' },
  { id: 'inv-004', sku: 'ODO-002', name: 'Anestesia lidocaína 2%', category: 'Medicamentos', unit: 'caja', quantity: 3, minimum: 5, supplier: 'Farmacia Dental', lot: 'LD-5581', expirationDate: '2026-12-02', unitCost: 24, location: 'Gabinete clínico · Nivel 1', notes: 'Almacenar según indicaciones del fabricante.' },
  { id: 'inv-005', sku: 'INS-001', name: 'Espejo bucal #5', category: 'Instrumental', unit: 'unidad', quantity: 15, minimum: 5, supplier: 'Instrumentos Odontológicos PTY', lot: '', expirationDate: '', unitCost: 3.8, location: 'Central de instrumental', notes: '' },
  { id: 'inv-006', sku: 'ODO-003', name: 'Algodón en rollo', category: 'Material odontológico', unit: 'paquete', quantity: 2, minimum: 5, supplier: 'Depósito Dental Central', lot: 'ALG-551', expirationDate: '2028-05-30', unitCost: 4.5, location: 'Almacén A · Estante 2', notes: '' },
]

function persist() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(products.value))
    localStorage.setItem(MOVEMENTS_KEY, JSON.stringify(movements.value))
    return true
  } catch (error) {
    console.error('No se pudo guardar el inventario', error)
    $q.notify({ type: 'negative', message: 'No se pudo guardar el inventario en este navegador.' })
    return false
  }
}

onMounted(() => {
  try {
    const savedProducts = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null')
    const savedMovements = JSON.parse(localStorage.getItem(MOVEMENTS_KEY) || '[]')
    products.value = Array.isArray(savedProducts) ? savedProducts : seedProducts
    movements.value = Array.isArray(savedMovements) ? savedMovements : []
  } catch (error) {
    products.value = seedProducts
    movements.value = []
    console.error('No se pudo leer el inventario local', error)
  }
})

function isExpired(product) {
  return Boolean(product.expirationDate && product.expirationDate < today())
}

function isExpiringSoon(product) {
  if (!product.expirationDate || isExpired(product)) return false
  const limit = new Date()
  limit.setDate(limit.getDate() + 90)
  return new Date(`${product.expirationDate}T23:59:59`) <= limit
}

function today() {
  return new Date().toISOString().slice(0, 10)
}

function stockState(product) {
  if (product.quantity <= 0) return 'Agotado'
  if (product.quantity <= product.minimum) return 'Stock bajo'
  return 'Disponible'
}

const activeProducts = computed(() => products.value.filter((product) => !product.archived))
const hasDemoProducts = computed(() => products.value.some((product) => String(product.id).startsWith('inv-00')))
const lowStockCount = computed(() => activeProducts.value.filter((product) => product.quantity <= product.minimum).length)
const expiredCount = computed(() => activeProducts.value.filter(isExpired).length)
const expiringSoonCount = computed(() => activeProducts.value.filter(isExpiringSoon).length)
const inventoryValue = computed(() => activeProducts.value.reduce((sum, product) => sum + Number(product.quantity || 0) * Number(product.unitCost || 0), 0))

const filteredProducts = computed(() => {
  const query = normalize(searchQuery.value)
  return activeProducts.value.filter((product) => {
    const matchesText = !query || normalize(`${product.sku} ${product.name} ${product.category} ${product.supplier} ${product.lot}`).includes(query)
    const matchesCategory = !selectedCategory.value || product.category === selectedCategory.value
    const state = stockState(product)
    const matchesStock = stockFilter.value === 'todos'
      || (stockFilter.value === 'bajo' && state !== 'Disponible')
      || (stockFilter.value === 'disponible' && state === 'Disponible')
      || (stockFilter.value === 'vencimiento' && (isExpired(product) || isExpiringSoon(product)))
    return matchesText && matchesCategory && matchesStock
  })
})

const recentMovements = computed(() => [...movements.value].sort((a, b) => `${b.date}${b.createdAt || ''}`.localeCompare(`${a.date}${a.createdAt || ''}`)))

function normalize(value) {
  return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es').trim()
}

function money(value) {
  return new Intl.NumberFormat('es-PA', { style: 'currency', currency: 'USD' }).format(Number(value) || 0)
}

function dateLabel(value) {
  if (!value) return 'Sin fecha'
  return new Intl.DateTimeFormat('es-PA', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`))
}

function stateClass(product) {
  if (isExpired(product)) return 'state-expired'
  const state = stockState(product)
  return state === 'Disponible' ? 'state-ok' : state === 'Agotado' ? 'state-out' : 'state-low'
}

function expirationLabel(product) {
  if (!product.expirationDate) return 'No aplica'
  if (isExpired(product)) return 'Vencido'
  if (isExpiringSoon(product)) return 'Próximo a vencer'
  return dateLabel(product.expirationDate)
}

function openNewProduct() {
  editingId.value = null
  productForm.value = emptyProduct()
  productDialog.value = true
}

function openEditProduct(product) {
  editingId.value = product.id
  productForm.value = { ...emptyProduct(), ...product }
  productDialog.value = true
}

function saveProduct() {
  const form = productForm.value
  if (!form.name.trim() || !form.category || !form.sku.trim()) {
    $q.notify({ type: 'warning', message: 'Completa el código, nombre y categoría del producto.' })
    return
  }
  const duplicateSku = activeProducts.value.some((item) => normalize(item.sku) === normalize(form.sku) && item.id !== editingId.value)
  if (duplicateSku) {
    $q.notify({ type: 'warning', message: 'Ya existe un producto con ese código.' })
    return
  }

  const quantity = Math.max(0, Number(form.quantity) || 0)
  const product = {
    ...form,
    id: editingId.value || `inv-${Date.now()}`,
    sku: form.sku.trim(),
    name: form.name.trim(),
    quantity,
    minimum: Math.max(0, Number(form.minimum) || 0),
    unitCost: Math.max(0, Number(form.unitCost) || 0),
    updatedAt: new Date().toISOString(),
  }
  const existing = products.value.find((item) => item.id === editingId.value)
  products.value = existing
    ? products.value.map((item) => item.id === editingId.value ? product : item)
    : [product, ...products.value]

  if (!existing && quantity > 0) {
    movements.value.unshift({
      id: `mov-${Date.now()}`, productId: product.id, sku: product.sku, productName: product.name,
      type: 'Inventario inicial', quantity, date: today(), reference: '', notes: 'Existencia inicial del producto', createdAt: new Date().toISOString(),
    })
  }
  if (persist()) {
    productDialog.value = false
    $q.notify({ type: 'positive', message: existing ? 'Producto actualizado.' : 'Producto agregado al inventario.' })
  }
}

function openMovement(product, type = 'entrada') {
  movementProduct.value = product
  movementForm.value = { ...emptyMovement(), type }
  movementDialog.value = true
}

function saveMovement() {
  const form = movementForm.value
  const product = movementProduct.value
  const amount = Number(form.quantity)
  if (!product || !Number.isFinite(amount) || amount <= 0 || !form.date) {
    $q.notify({ type: 'warning', message: 'Indica una cantidad mayor que cero y una fecha válida.' })
    return
  }
  if (form.type === 'salida' && amount > product.quantity) {
    $q.notify({ type: 'warning', message: 'La salida supera las existencias disponibles.' })
    return
  }

  const updatedProduct = {
    ...product,
    quantity: form.type === 'entrada' ? Number(product.quantity) + amount : Number(product.quantity) - amount,
    updatedAt: new Date().toISOString(),
  }
  products.value = products.value.map((item) => item.id === product.id ? updatedProduct : item)
  movements.value.unshift({
    id: `mov-${Date.now()}`, productId: product.id, sku: product.sku, productName: product.name,
    type: form.type === 'entrada' ? 'Entrada' : 'Salida', quantity: amount, date: form.date,
    reference: form.reference.trim(), notes: form.notes.trim(), createdAt: new Date().toISOString(),
  })
  if (persist()) {
    movementDialog.value = false
    $q.notify({ type: 'positive', message: `${form.type === 'entrada' ? 'Entrada' : 'Salida'} registrada. Existencias actualizadas.` })
  }
}

function archiveProduct(product) {
  $q.dialog({
    title: 'Retirar producto',
    message: `¿Quieres retirar “${product.name}” del inventario activo? Su historial de movimientos se conservará.`,
    cancel: { flat: true, label: 'Volver', noCaps: true },
    ok: { color: 'negative', label: 'Retirar', noCaps: true },
    persistent: true,
  }).onOk(() => {
    products.value = products.value.map((item) => item.id === product.id ? { ...item, archived: true } : item)
    if (persist()) $q.notify({ type: 'positive', message: 'Producto retirado del inventario activo.' })
  })
}

const productColumns = [
  { name: 'product', label: 'Producto', field: 'name', align: 'left', sortable: true },
  { name: 'category', label: 'Categoría', field: 'category', align: 'left', sortable: true },
  { name: 'quantity', label: 'Existencias', field: 'quantity', align: 'center', sortable: true },
  { name: 'expiration', label: 'Vencimiento', field: 'expirationDate', align: 'left', sortable: true },
  { name: 'cost', label: 'Costo unitario', field: 'unitCost', align: 'right', sortable: true },
  { name: 'actions', label: '', field: 'actions', align: 'right' },
]

const movementColumns = [
  { name: 'date', label: 'Fecha', field: 'date', align: 'left', sortable: true },
  { name: 'product', label: 'Producto', field: 'productName', align: 'left', sortable: true },
  { name: 'type', label: 'Movimiento', field: 'type', align: 'center' },
  { name: 'quantity', label: 'Cantidad', field: 'quantity', align: 'center' },
  { name: 'reference', label: 'Referencia', field: 'reference', align: 'left' },
  { name: 'notes', label: 'Detalle', field: 'notes', align: 'left' },
]
</script>

<template>
  <q-page class="inventory-page futuristic-bg q-pa-md q-pa-lg-lg">
    <section class="page-heading">
      <div>
        <h1>Inventario</h1>
        <p>Controla insumos, existencias y movimientos de la clínica.</p>
      </div>
      <q-btn unelevated no-caps icon="add" label="Agregar producto" class="primary-action" @click="openNewProduct" />
    </section>

    <div v-if="hasDemoProducts" class="demo-notice">
      <q-icon name="info" />
      <span>Incluye productos de demostración para mostrar el módulo. Verifica sus datos antes de usar el inventario de
        la clínica.</span>
    </div>

    <section class="inventory-stats">
      <article class="inventory-stat-card">
        <span class="stat-icon"><q-icon name="inventory_2" /></span>
        <div><small>Productos activos</small><strong>{{ activeProducts.length }}</strong><span>En el catálogo</span>
        </div>
      </article>
      <article class="inventory-stat-card" :class="{ 'has-alert': lowStockCount }">
        <span class="stat-icon"><q-icon name="production_quantity_limits" /></span>
        <div><small>Stock bajo</small><strong>{{ lowStockCount }}</strong><span>En mínimo o agotados</span></div>
      </article>
      <article class="inventory-stat-card" :class="{ 'has-alert': expiredCount || expiringSoonCount }">
        <span class="stat-icon"><q-icon name="event_busy" /></span>
        <div><small>Vencimientos</small><strong>{{ expiredCount + expiringSoonCount }}</strong><span>{{ expiredCount }}
            vencidos · {{ expiringSoonCount }} próximos</span></div>
      </article>
      <article class="inventory-stat-card">
        <span class="stat-icon"><q-icon name="payments" /></span>
        <div><small>Valor estimado</small><strong>{{ money(inventoryValue) }}</strong><span>Existencias actuales</span>
        </div>
      </article>
    </section>

    <section class="inventory-panel">
      <header class="panel-header">
        <div>
          <div class="eyebrow">Almacén</div>
          <h2>Control de inventario</h2>
        </div>
        <q-tabs v-model="activeTab" dense no-caps class="inventory-tabs" active-color="cyan-3" indicator-color="cyan-4">
          <q-tab name="products" icon="category" label="Productos" />
          <q-tab name="movements" icon="swap_vert" label="Movimientos" />
        </q-tabs>
      </header>

      <q-tab-panels v-model="activeTab" animated class="inventory-tab-panels">
        <q-tab-panel name="products" class="q-pa-none">
          <div class="inventory-filters">
            <q-input v-model="searchQuery" outlined dark dense clearable
              label="Buscar producto, código, lote o proveedor" class="inventory-search">
              <template #prepend><q-icon name="search" /></template>
            </q-input>
            <q-select v-model="selectedCategory" outlined dark dense clearable :options="categoryOptions"
              label="Todas las categorías" class="inventory-filter" />
            <q-select v-model="stockFilter" outlined dark dense emit-value map-options :options="[
              { label: 'Todos los estados', value: 'todos' }, { label: 'Stock bajo o agotado', value: 'bajo' },
              { label: 'Disponible', value: 'disponible' }, { label: 'Vencimiento próximo', value: 'vencimiento' },
            ]" label="Estado" class="inventory-filter" />
          </div>

          <q-table :rows="filteredProducts" :columns="productColumns" row-key="id" dark flat
            :pagination="{ rowsPerPage: 8 }" class="inventory-table">
            <template #body-cell-product="props">
              <q-td :props="props">
                <div class="product-cell"><span class="product-icon"><q-icon name="inventory_2" /></span>
                  <div><strong>{{ props.row.name }}</strong><small>{{ props.row.sku }} · {{ props.row.location ||
                      'Ubicación sin indicar' }}</small></div>
                </div>
              </q-td>
            </template>
            <template #body-cell-category="props"><q-td :props="props"><span class="category-label">{{
              props.row.category }}</span></q-td></template>
            <template #body-cell-quantity="props">
              <q-td :props="props">
                <div class="stock-cell"><strong>{{ props.row.quantity }} <small>{{ props.row.unit }}</small></strong>
                  <span :class="['stock-badge', stateClass(props.row)]">{{ stockState(props.row) }}</span>
                </div>
              </q-td>
            </template>
            <template #body-cell-expiration="props">
              <q-td :props="props"><span
                  :class="{ 'expiration-alert': isExpired(props.row) || isExpiringSoon(props.row) }">{{
                    expirationLabel(props.row) }}</span></q-td>
            </template>
            <template #body-cell-cost="props"><q-td :props="props">{{ money(props.row.unitCost) }}</q-td></template>
            <template #body-cell-actions="props">
              <q-td :props="props">
                <div class="row-actions">
                  <q-btn flat round dense icon="add_box" aria-label="Registrar entrada" class="action-icon"
                    @click="openMovement(props.row, 'entrada')"><q-tooltip>Registrar entrada</q-tooltip></q-btn>
                  <q-btn flat round dense icon="outbox" aria-label="Registrar salida" class="action-icon"
                    @click="openMovement(props.row, 'salida')"><q-tooltip>Registrar salida</q-tooltip></q-btn>
                  <q-btn flat round dense icon="edit" aria-label="Editar producto" class="action-icon"
                    @click="openEditProduct(props.row)"><q-tooltip>Editar producto</q-tooltip></q-btn>
                  <q-btn flat round dense icon="archive" aria-label="Retirar producto" class="action-icon danger-icon"
                    @click="archiveProduct(props.row)"><q-tooltip>Retirar del inventario</q-tooltip></q-btn>
                </div>
              </q-td>
            </template>
            <template #no-data>
              <div class="empty-inventory"><q-icon name="inventory_2" /><strong>No hay productos para
                  mostrar</strong><span>Ajusta los filtros o agrega un producto al inventario.</span></div>
            </template>
          </q-table>
        </q-tab-panel>

        <q-tab-panel name="movements" class="q-pa-none">
          <div class="movement-summary"><q-icon name="history" /><span>Historial de entradas y salidas del
              inventario.</span><q-space /><q-badge>{{ movements.length }} movimientos</q-badge></div>
          <q-table :rows="recentMovements" :columns="movementColumns" row-key="id" dark flat
            :pagination="{ rowsPerPage: 10 }" class="inventory-table">
            <template #body-cell-date="props"><q-td :props="props">{{ dateLabel(props.row.date) }}</q-td></template>
            <template #body-cell-type="props"><q-td :props="props"><span
                  :class="['movement-badge', props.row.type.toLowerCase().includes('entrada') || props.row.type.includes('inicial') ? 'movement-in' : 'movement-out']">{{
                  props.row.type }}</span></q-td></template>
            <template #body-cell-quantity="props"><q-td :props="props"><strong>{{
              props.row.type.toLowerCase().includes('salida') ? '−' : '+' }}{{ props.row.quantity
                  }}</strong></q-td></template>
            <template #no-data>
              <div class="empty-inventory"><q-icon name="swap_vert" /><strong>Aún no hay movimientos</strong><span>Las
                  entradas y salidas que registres aparecerán aquí.</span></div>
            </template>
          </q-table>
        </q-tab-panel>
      </q-tab-panels>
    </section>

    <q-dialog v-model="productDialog" persistent>
      <q-card class="inventory-dialog">
        <header class="inventory-dialog-header">
          <span class="dialog-icon"><q-icon :name="editingId ? 'edit_note' : 'add_box'" /></span>
          <div>
            <div class="eyebrow">Catálogo de productos</div>
            <h2>{{ editingId ? 'Editar producto' : 'Agregar producto' }}</h2>
            <p>Identificación, existencias y datos de almacenamiento.</p>
          </div>
          <q-btn flat round dense icon="close" class="dialog-close" aria-label="Cerrar"
            @click="productDialog = false" />
        </header>
        <q-form class="inventory-form" @submit.prevent="saveProduct">
          <div class="inventory-form-grid">
            <q-input v-model.trim="productForm.sku" outlined dark dense label="Código / SKU *" />
            <q-input v-model.trim="productForm.name" outlined dark dense label="Nombre del producto *" />
            <q-select v-model="productForm.category" outlined dark dense use-input new-value-mode="add-unique"
              :options="categories" label="Categoría *" />
            <q-select v-model="productForm.unit" outlined dark dense :options="units" label="Unidad de medida" />
            <q-input v-model.number="productForm.quantity" outlined dark dense type="number" min="0"
              label="Existencias actuales" :disable="Boolean(editingId)"
              hint="Para ajustar stock usa Registrar entrada/salida." />
            <q-input v-model.number="productForm.minimum" outlined dark dense type="number" min="0"
              label="Nivel mínimo de stock" />
            <q-input v-model.trim="productForm.supplier" outlined dark dense label="Proveedor" />
            <q-input v-model.trim="productForm.location" outlined dark dense label="Ubicación" />
            <q-input v-model.trim="productForm.lot" outlined dark dense label="Lote" />
            <q-input v-model="productForm.expirationDate" outlined dark dense type="date" label="Fecha de vencimiento"
              stack-label />
            <q-input v-model.number="productForm.unitCost" outlined dark dense type="number" min="0" step="0.01"
              prefix="$" label="Costo unitario estimado" />
            <q-input v-model.trim="productForm.notes" outlined dark dense type="textarea" autogrow label="Notas"
              class="form-full" />
          </div>
          <footer class="inventory-dialog-footer"><q-btn flat no-caps label="Cancelar" class="subtle-action"
              @click="productDialog = false" /><q-btn unelevated no-caps
              :label="editingId ? 'Guardar cambios' : 'Agregar producto'" icon="check" class="primary-action"
              type="submit" /></footer>
        </q-form>
      </q-card>
    </q-dialog>

    <q-dialog v-model="movementDialog" persistent>
      <q-card class="inventory-dialog movement-dialog">
        <header class="inventory-dialog-header">
          <span class="dialog-icon"><q-icon :name="movementForm.type === 'entrada' ? 'add_box' : 'outbox'" /></span>
          <div>
            <div class="eyebrow">{{ movementForm.type === 'entrada' ? 'Reposición' : 'Consumo clínico' }}</div>
            <h2>Registrar {{ movementForm.type }}</h2>
            <p>{{ movementProduct?.name }} · Existencias: {{ movementProduct?.quantity }} {{ movementProduct?.unit }}
            </p>
          </div>
          <q-btn flat round dense icon="close" class="dialog-close" aria-label="Cerrar"
            @click="movementDialog = false" />
        </header>
        <q-form class="inventory-form" @submit.prevent="saveMovement">
          <div class="inventory-form-grid">
            <q-select v-model="movementForm.type" outlined dark dense emit-value map-options
              :options="[{ label: 'Entrada', value: 'entrada' }, { label: 'Salida', value: 'salida' }]"
              label="Tipo de movimiento" />
            <q-input v-model.number="movementForm.quantity" outlined dark dense type="number" min="1" step="1"
              label="Cantidad" />
            <q-input v-model="movementForm.date" outlined dark dense type="date" stack-label label="Fecha" />
            <q-input v-model.trim="movementForm.reference" outlined dark dense label="Referencia / factura" />
            <q-input v-model.trim="movementForm.notes" outlined dark dense type="textarea" autogrow
              label="Detalle u observaciones" class="form-full" />
          </div>
          <footer class="inventory-dialog-footer"><q-btn flat no-caps label="Cancelar" class="subtle-action"
              @click="movementDialog = false" /><q-btn unelevated no-caps label="Guardar movimiento" icon="check"
              class="primary-action" type="submit" /></footer>
        </q-form>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<style scoped>
.inventory-page {
  min-height: 100%;
  color: #e2e8f0;
}

.page-heading,
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.page-heading {
  max-width: 1200px;
  margin: 4px auto 24px;
}

.page-heading h1 {
  margin: 4px 0;
  color: #f8fafc;
  font-size: clamp(26px, 4vw, 34px);
  font-weight: 700;
}

.page-heading p,
.inventory-dialog-header p {
  margin: 0;
  color: #94a3b8;
  font-size: 13px;
}

.eyebrow {
  color: #67e8f9;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .18em;
  text-transform: uppercase;
}

.primary-action {
  min-height: 40px;
  padding: 0 15px;
  border: 1px solid rgba(34, 211, 238, .4);
  border-radius: 9px;
  background: linear-gradient(120deg, rgba(8, 145, 178, .32), rgba(30, 64, 175, .28));
  color: #a5f3fc;
}

.demo-notice {
  display: flex;
  max-width: 1200px;
  align-items: center;
  gap: 9px;
  margin: -10px auto 17px;
  padding: 10px 13px;
  border: 1px solid rgba(251, 191, 36, .22);
  border-radius: 9px;
  background: rgba(120, 83, 12, .1);
  color: #cbd5e1;
  font-size: 10px;
}

.demo-notice .q-icon {
  flex: 0 0 auto;
  color: #fcd34d;
}

.inventory-stats {
  display: grid;
  max-width: 1200px;
  margin: 0 auto 18px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.inventory-stat-card {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 13px;
  padding: 17px;
  border: 1px solid rgba(100, 140, 190, .18);
  border-radius: 14px;
  background: rgba(16, 19, 31, .78);
}

.inventory-stat-card.has-alert {
  border-color: rgba(248, 113, 113, .32);
}

.stat-icon,
.dialog-icon {
  display: grid;
  width: 43px;
  height: 43px;
  flex: 0 0 43px;
  place-items: center;
  border: 1px solid rgba(34, 211, 238, .2);
  border-radius: 12px;
  background: rgba(8, 145, 178, .1);
  color: #67e8f9;
  font-size: 21px;
}

.has-alert .stat-icon {
  border-color: rgba(248, 113, 113, .24);
  background: rgba(127, 29, 29, .13);
  color: #fca5a5;
}

.inventory-stat-card>div {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 3px;
}

.inventory-stat-card small {
  color: #94a3b8;
  font-size: 10px;
}

.inventory-stat-card strong {
  overflow: hidden;
  color: #f1f5f9;
  font-size: 21px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.inventory-stat-card span:not(.stat-icon) {
  color: #64748b;
  font-size: 9px;
}

.inventory-panel {
  max-width: 1200px;
  margin: 0 auto;
  padding: 22px;
  border: 1px solid rgba(100, 140, 190, .22);
  border-radius: 17px;
  background: rgba(16, 19, 31, .82);
  box-shadow: 0 0 35px rgba(37, 99, 235, .05);
}

.panel-header {
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.panel-header h2 {
  margin: 5px 0 0;
  color: #f1f5f9;
  font-size: 18px;
  font-weight: 650;
}

.inventory-tabs {
  color: #94a3b8;
}

.inventory-tab-panels {
  background: transparent;
  color: inherit;
}

.inventory-filters {
  display: grid;
  margin: 10px 0 14px;
  grid-template-columns: minmax(220px, 1.6fr) minmax(170px, 1fr) minmax(160px, .8fr);
  gap: 10px;
}

.inventory-search :deep(.q-field__control),
.inventory-filter :deep(.q-field__control) {
  border-radius: 9px;
  background: rgba(15, 23, 42, .46);
}

.inventory-search :deep(.q-field__label),
.inventory-search :deep(.q-field__native),
.inventory-search :deep(.q-field__marginal),
.inventory-filter :deep(.q-field__label),
.inventory-filter :deep(.q-field__native),
.inventory-filter :deep(.q-field__marginal) {
  color: #b6c4d5;
}

.inventory-search :deep(.q-field--outlined .q-field__control:before),
.inventory-filter :deep(.q-field--outlined .q-field__control:before) {
  border-color: rgba(100, 140, 190, .26);
}

.inventory-table {
  background: transparent;
  color: #cbd5e1;
}

.inventory-table :deep(thead tr th) {
  color: #67e8f9;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .06em;
  text-transform: uppercase;
}

.inventory-table :deep(tbody td) {
  border-color: rgba(100, 140, 190, .11);
  font-size: 11px;
}

.inventory-table :deep(.q-table__bottom) {
  color: #94a3b8;
}

.product-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 190px;
}

.product-icon {
  display: grid;
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  place-items: center;
  border: 1px solid rgba(34, 211, 238, .17);
  border-radius: 9px;
  background: rgba(8, 145, 178, .1);
  color: #67e8f9;
}

.product-cell>div {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.product-cell strong {
  color: #e2e8f0;
  font-size: 11px;
  font-weight: 600;
}

.product-cell small {
  color: #64748b;
  font-size: 9px;
}

.category-label {
  color: #aab8ca;
  font-size: 10px;
}

.stock-cell {
  display: flex;
  align-items: center;
  gap: 7px;
  justify-content: center;
  white-space: nowrap;
}

.stock-cell>strong {
  color: #e2e8f0;
  font-size: 12px;
}

.stock-cell small {
  color: #64748b;
  font-size: 9px;
  font-weight: 400;
}

.stock-badge,
.movement-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 7px;
  border: 1px solid transparent;
  border-radius: 20px;
  font-size: 9px;
  white-space: nowrap;
}

.state-ok {
  border-color: rgba(34, 197, 94, .25);
  background: rgba(34, 197, 94, .1);
  color: #86efac;
}

.state-low {
  border-color: rgba(251, 191, 36, .28);
  background: rgba(161, 98, 7, .13);
  color: #fcd34d;
}

.state-out,
.state-expired {
  border-color: rgba(248, 113, 113, .28);
  background: rgba(127, 29, 29, .15);
  color: #fca5a5;
}

.expiration-alert {
  color: #fca5a5;
}

.row-actions {
  display: flex;
  justify-content: flex-end;
  white-space: nowrap;
}

.action-icon {
  color: #94a3b8;
}

.action-icon:hover {
  color: #67e8f9;
  background: rgba(34, 211, 238, .08);
}

.danger-icon:hover {
  color: #fca5a5;
  background: rgba(248, 113, 113, .08);
}

.empty-inventory {
  display: flex;
  width: 100%;
  align-items: center;
  flex-direction: column;
  gap: 8px;
  padding: 42px 18px;
  color: #64748b;
}

.empty-inventory>.q-icon {
  color: #67e8f9;
  font-size: 29px;
}

.empty-inventory strong {
  color: #cbd5e1;
  font-size: 13px;
}

.empty-inventory span {
  font-size: 11px;
  text-align: center;
}

.movement-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 13px 3px;
  color: #94a3b8;
  font-size: 11px;
}

.movement-summary>.q-icon {
  color: #67e8f9;
}

.movement-summary :deep(.q-badge) {
  border: 1px solid rgba(34, 211, 238, .2);
  background: rgba(8, 145, 178, .12);
  color: #a5f3fc;
}

.movement-in {
  border-color: rgba(34, 197, 94, .23);
  background: rgba(34, 197, 94, .1);
  color: #86efac;
}

.movement-out {
  border-color: rgba(251, 191, 36, .23);
  background: rgba(161, 98, 7, .12);
  color: #fcd34d;
}

.inventory-dialog {
  width: min(720px, calc(100vw - 28px));
  max-width: 720px;
  max-height: 90vh;
  overflow: hidden;
  border: 1px solid rgba(34, 211, 238, .28);
  border-radius: 17px;
  background: radial-gradient(ellipse at 5% 0%, rgba(8, 145, 178, .16), transparent 42%), #0b1120;
  color: #e2e8f0;
  box-shadow: 0 24px 80px rgba(0, 0, 0, .58);
}

.inventory-dialog-header {
  display: flex;
  align-items: center;
  gap: 13px;
  padding: 20px 22px;
  border-bottom: 1px solid rgba(100, 140, 190, .15);
}

.inventory-dialog-header>div {
  min-width: 0;
  flex: 1;
}

.inventory-dialog-header h2 {
  margin: 4px 0;
  color: #f8fafc;
  font-size: 19px;
  font-weight: 650;
}

.inventory-dialog-header p {
  font-size: 11px;
}

.dialog-close {
  align-self: flex-start;
  color: #94a3b8;
}

.inventory-form {
  max-height: calc(90vh - 90px);
  overflow-y: auto;
}

.inventory-form-grid {
  display: grid;
  padding: 20px 22px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.inventory-form-grid :deep(.q-field__control) {
  border-radius: 9px;
  background: rgba(15, 23, 42, .46);
}

.inventory-form-grid :deep(.q-field__label),
.inventory-form-grid :deep(.q-field__native),
.inventory-form-grid :deep(.q-field__marginal),
.inventory-form-grid :deep(.q-field__prefix) {
  color: #b6c4d5;
}

.inventory-form-grid :deep(.q-field--outlined .q-field__control:before) {
  border-color: rgba(100, 140, 190, .28);
}

.inventory-form-grid :deep(.q-field--focused .q-field__control:after) {
  border-color: #22d3ee;
}

.form-full {
  grid-column: 1 / -1;
}

.inventory-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 9px;
  padding: 13px 22px;
  border-top: 1px solid rgba(100, 140, 190, .14);
  background: rgba(2, 6, 23, .28);
}

.subtle-action {
  color: #9fb0c5;
}

@media (max-width: 900px) {
  .inventory-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .inventory-filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .inventory-search {
    grid-column: 1 / -1;
  }
}

@media (max-width: 600px) {
  .page-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .page-heading .primary-action {
    width: 100%;
    justify-content: center;
  }

  .inventory-stats {
    gap: 8px;
  }

  .inventory-stat-card {
    align-items: flex-start;
    flex-direction: column;
    padding: 12px;
    gap: 9px;
  }

  .inventory-stat-card strong {
    font-size: 18px;
  }

  .inventory-panel {
    padding: 13px;
  }

  .panel-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .inventory-tabs {
    width: 100%;
  }

  .inventory-tabs :deep(.q-tab) {
    flex: 1;
  }

  .inventory-filters {
    grid-template-columns: 1fr;
  }

  .inventory-search {
    grid-column: auto;
  }

  .inventory-form-grid {
    grid-template-columns: 1fr;
    padding: 16px;
  }

  .form-full {
    grid-column: auto;
  }

  .inventory-dialog-header {
    padding: 17px 16px;
  }

  .inventory-dialog-footer {
    padding: 12px 16px;
  }

  .movement-summary {
    flex-wrap: wrap;
  }
}
</style>
