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
  const body = contentType.includes('application/json')
    ? await response.json()
    : await response.text()

  if (!response.ok) {
    const message = typeof body === 'object' && body?.detail
      ? body.detail
      : `Ошибка API (${response.status})`
    throw new Error(message)
  }
  return body
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
  const dishes = await request('/dishes')
  return dishes.map(dish => ({
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
  }))
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
    ingredients: dish.ingredients || [],
    steps: dish.recipe?.steps || [],
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
