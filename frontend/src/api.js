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

  // If 401 Unauthorized, try refreshing the token once before failing
  if (response.status === 401 && path !== '/auth/login' && path !== '/auth/refresh') {
    const refreshToken = localStorage.getItem('meal_planner_refresh_token')
    if (refreshToken) {
      try {
        const refreshRes = await fetch(`${API_URL}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        })
        if (refreshRes.ok) {
          const newTokens = await refreshRes.json()
          localStorage.setItem('meal_planner_access_token', newTokens.access_token)
          localStorage.setItem('meal_planner_refresh_token', newTokens.refresh_token)
          headers.Authorization = `Bearer ${newTokens.access_token}`
          const retryResponse = await fetch(`${API_URL}${path}`, { ...options, headers })
          if (retryResponse.ok) {
            const retryText = await retryResponse.text()
            return retryText.trim() ? JSON.parse(retryText) : null
          }
        }
      } catch (err) {
        // silent refresh error
      }
    }

    // Refresh failed or invalid session: clear stale tokens and redirect to login
    clearSession()
    if (typeof window !== 'undefined' && window.location.pathname !== '/login' && window.location.pathname !== '/register') {
      window.location.replace('/login')
    }
  }

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

export async function getCurrentUser() {
  return request('/auth/me')
}

export async function register(data) {
  await request('/auth/register', { method: 'POST', body: JSON.stringify(data) })
  return login(data.email, data.password)
}

export async function getRecipes() {
  const dishes = await request('/dishes')
  const items = Array.isArray(dishes) ? dishes : (dishes.items || [])
  const catMap = { breakfast: 'Завтрак', lunch: 'Обед', dinner: 'Ужин', snack: 'Перекус' }
  return items.map(dish => ({
    id: dish.id,
    title: dish.name || dish.title,
    category: dish.category || catMap[dish.meal_type] || dish.meal_type,
    meal_type: dish.meal_type,
    tag: dish.recipe?.tag || (dish.tags && dish.tags[0]) || '',
    time: dish.cooking_time || dish.recipe?.time || dish.time || 20,
    calories: dish.calories,
    price: dish.cost ?? dish.price,
    protein: dish.protein ?? dish.proteins,
    fat: dish.fat ?? dish.fats,
    carbs: dish.carbs,
    image: dish.image_url,
    description: dish.description || dish.recipe?.description || '',
    ingredients: dish.ingredients || dish.recipe?.ingredients || [],
    steps: dish.recipe?.steps || [],
    tags: dish.tags || [],
  }))
}

export async function getRecipe(id) {
  const dish = await request(`/dishes/${encodeURIComponent(id)}`)
  return {
    id: dish.id,
    title: dish.name,
    category: dish.category,
    meal_type: dish.meal_type,
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

export async function estimateDishPrice({ dish_name, category, ingredients }) {
  return request('/ai/estimate-price', {
    method: 'POST',
    body: JSON.stringify({
      dish_name,
      category,
      ingredients: ingredients || [],
    }),
  })
}

export async function suggestDishImage({ dish_name, category }) {
  return request('/ai/suggest-image', {
    method: 'POST',
    body: JSON.stringify({
      dish_name,
      category,
    }),
  })
}

export async function consultAssistant(query) {
  return request('/ai/consult', {
    method: 'POST',
    body: JSON.stringify({ query }),
  })
}

export async function estimateIngredientsPrice({ dish_name, ingredients }) {
  return request('/ai/estimate-ingredients-price', {
    method: 'POST',
    body: JSON.stringify({
      dish_name,
      ingredients: ingredients || [],
    }),
  })
}

export async function estimateNutrition({ dish_name, ingredients }) {
  return request('/ai/estimate-nutrition', {
    method: 'POST',
    body: JSON.stringify({
      dish_name,
      ingredients: ingredients || [],
    }),
  })
}

export async function generateCookingSteps({ dish_name, ingredients }) {
  return request('/ai/generate-cooking-steps', {
    method: 'POST',
    body: JSON.stringify({
      dish_name,
      ingredients: ingredients || [],
    }),
  })
}

export async function estimateCookingTime({ dish_name, steps, ingredients }) {
  return request('/ai/estimate-cooking-time', {
    method: 'POST',
    body: JSON.stringify({
      dish_name,
      steps: steps || [],
      ingredients: ingredients || [],
    }),
  })
}

export async function generateFullRecipe({ dish_name, category }) {
  return request('/ai/generate-full-recipe', {
    method: 'POST',
    body: JSON.stringify({
      dish_name,
      category,
    }),
  })
}


