const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1'

export function getAccessToken() {
  return localStorage.getItem('meal_planner_access_token')
}

export function clearSession() {
  localStorage.removeItem('meal_planner_access_token')
  localStorage.removeItem('meal_planner_refresh_token')
  localStorage.removeItem('meal_planner_user')
}

async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) }
  const token = getAccessToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const response = await fetch(`${API_URL}${path}`, { ...options, headers })
  const contentType = response.headers.get('content-type') || ''
  const rawBody = await response.text()
  const body = contentType.includes('application/json') && rawBody.trim()
    ? JSON.parse(rawBody)
    : rawBody

  if (!response.ok) {
    const message = typeof body === 'object' && body?.detail
      ? body.detail
      : `Ошибка API (${response.status})`
    throw new Error(message)
  }
  return response.status === 204 ? null : body
}

export async function login(email, password) {
  const tokens = await request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
  localStorage.setItem('meal_planner_access_token', tokens.access_token)
  localStorage.setItem('meal_planner_refresh_token', tokens.refresh_token)
  const user = await request('/auth/me')
  localStorage.setItem('meal_planner_user', JSON.stringify(user))
  return user
}

export async function register(data) {
  await request('/auth/register', { method: 'POST', body: JSON.stringify(data) })
  return login(data.email, data.password)
}

export async function getRecipes() {
  const firstPage = await request('/dishes?page=1&page_size=50')
  if (Array.isArray(firstPage)) return firstPage.map(mapDish)
  const pages = await Promise.all(
    Array.from({ length: Math.max(0, (firstPage.pages || 1) - 1) }, (_, index) =>
      request(`/dishes?page=${index + 2}&page_size=50`)
    )
  )
  const items = [firstPage, ...pages].flatMap(page => page.items || [])
  return items.map(mapDish)
}

function mapDish(dish) {
  return {
    id: dish.id,
    title: dish.name,
    category: dish.meal_type,
    tag: dish.recipe?.tag || '',
    time: dish.recipe?.time || 0,
    calories: dish.calories,
    price: dish.price,
    protein: dish.proteins,
    fat: dish.fats,
    carbs: dish.carbs,
    image: dish.image_url,
    description: dish.recipe?.description || '',
    ingredients: dish.recipe?.ingredients || [],
    steps: dish.recipe?.steps || [],
    tags: dish.tags || [],
  }
}

export async function getRecipe(id) {
  const dish = await request(`/recipes/${encodeURIComponent(id)}`)
  return {
    id: dish.id,
    title: dish.name,
    category: dish.category,
    tag: dish.recipe?.tag || '',
    time: dish.cooking_time,
    calories: dish.calories,
    price: dish.cost,
    protein: dish.protein,
    fat: dish.fat,
    carbs: dish.carbs,
    image: dish.image_url,
    description: dish.description,
    instructions: dish.instructions || '',
    ingredients: dish.ingredients || [],
    steps: dish.recipe?.steps || [],
    tags: dish.tags || [],
  }
}

export async function createRecipe(data) {
  return request('/moderator/recipes', {
    method: 'POST',
    body: JSON.stringify({
      ...data,
      ingredients: data.ingredients || [],
      steps: data.steps || [],
    }),
  })
}

export async function updateRecipe(id, data) {
  return request(`/moderator/recipes/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export async function deleteRecipe(id) {
  return request(`/moderator/recipes/${encodeURIComponent(id)}`, { method: 'DELETE' })
}

export async function getShoppingItems() {
  return request('/shopping')
}

export async function addShoppingItem(data) {
  return request('/shopping/items', { method: 'POST', body: JSON.stringify(data) })
}

export async function updateShoppingItem(id, data) {
  return request(`/shopping/items/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify(data) })
}

export async function deleteShoppingItem(id) {
  return request(`/shopping/items/${encodeURIComponent(id)}`, { method: 'DELETE' })
}

export async function deleteAllShoppingItems() {
  return request('/shopping', { method: 'DELETE' })
}

export async function addIngredientsToShopping(ingredients) {
  return Promise.all(ingredients.map(item => addShoppingItem({
    name: item.name,
    quantity: Number(item.quantity) || 1,
    unit: item.unit || 'шт.',
    price: Number(item.price) || 0,
    category: item.category || 'other',
  })))
}

export async function addMealToRation(rationId, data) {
  return request(`/rations/${encodeURIComponent(rationId)}/meals`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getProfile() {
  return request('/users/me/profile')
}

export async function updateProfile(data) {
  const user = await request('/users/me/profile', {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
  localStorage.setItem('meal_planner_user', JSON.stringify(user))
  return user
}

export async function generateRation(periodDays, tags, extraRequest = '', model) {
  return request('/rations/generate', {
    method: 'POST',
    body: JSON.stringify({ period_days: periodDays, tags, extra_request: extraRequest, model }),
  })
}

export async function getRations() {
  return request('/rations')
}

export async function getRationPlan(rationId) {
  return request(`/rations/${encodeURIComponent(rationId)}/plan`)
}

export async function getDiary() {
  return request('/diary')
}

export async function addDiaryEntry(data) {
  return request('/diary', { method: 'POST', body: JSON.stringify(data) })
}

export async function deleteDiaryEntry(id) {
  return request(`/diary/${encodeURIComponent(id)}`, { method: 'DELETE' })
}
