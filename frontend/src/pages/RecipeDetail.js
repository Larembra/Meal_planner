import React, { useEffect, useMemo, useState } from 'react'
import { Button, Card, ImageBox } from '../components/UI'
import { mealRecipes, recipes, sumIngredientPrices, ingredientText } from '../data/mockData'
import { addIngredientsToShopping, addMealToRation, getRations, getRecipe } from '../api'

export default function RecipeDetail() {
  const id = window.location.pathname.split('/').pop()
  const fallback = useMemo(() => [...recipes, ...mealRecipes].find(r => String(r.id) === id) || recipes[0], [id])
  const [recipe, setRecipe] = useState(fallback)
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  useEffect(() => {
    getRecipe(id).then(setRecipe).catch(() => setRecipe(fallback))
  }, [id, fallback])
  const addShopping = async () => {
    try {
      await addIngredientsToShopping(recipe.ingredients || [])
      setMessage("Ингредиенты добавлены в список покупок")
    } catch (err) { setError(err.message) }
  }
  const addToRation = async () => {
    try {
      const rations = await getRations()
      if (!rations.length) throw new Error("Сначала создайте рацион")
      const today = new Date().toISOString().slice(0, 10)
      await addMealToRation(rations[0].id, { meal_id: recipe.id, date: today, meal_type: recipe.category || "dinner", servings: 1 })
      setMessage("Блюдо добавлено в рацион")
    } catch (err) { setError(err.message) }
  }

  return (
    <div className="container recipe-detail">
      <a href="/recipes" className="back">
        ← Назад к рецептам
      </a>

      <div className="detail-grid">
        <div>
          <ImageBox
            src={recipe.image}
            className="detail-image"
          />

          <Card>
            <h3>Пищевая ценность (на порцию)</h3>

            <div className="nutrition">
              <strong>
                {recipe.calories}
                <small>калорий</small>
              </strong>

              <strong>
                {recipe.protein}г
                <small>белки</small>
              </strong>

              <strong>
                {recipe.fat}г
                <small>жиры</small>
              </strong>

              <strong>
                {recipe.carbs}г
                <small>углеводы</small>
              </strong>
            </div>
          </Card>

          <Card className="price-card">
            <h3>Стоимость блюда</h3>
            <strong>{sumIngredientPrices(recipe.ingredients) || recipe.price || 0} ₽</strong>
            <p>Сумма цен ингредиентов на порцию.</p>
          </Card>
        </div>

        <div className="recipe-detail-content">
          <div className="eyebrow">
            {recipe.category} ⏱ Время приготовления: {recipe.time} минут
          </div>

          <h1>{recipe.title}</h1>

          <Card>
            <h3>Ингредиенты (на 2 порции)</h3>

            <ul className="ingredient-list">
              {(recipe.ingredients || ['Ингредиенты указаны в рецепте']).map((item, i) => (
                <li key={ingredientText(item) || i}>
                  <span>{typeof item === 'string' ? item : item.name}</span>
                  {typeof item === 'object' && (
                    <span>
                      {item.quantity}
                      {item.price != null && item.price !== '' ? ` · ${item.price} ₽` : ''}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </Card>

          <div className="actions">
            <Button onClick={addToRation}>Добавить в рацион питания</Button>

            <Button variant="secondary" onClick={addShopping}>
              🛒 Добавить ингредиенты в покупки
            </Button>
          </div>
          {message && <p className="success">{message}</p>}
          {error && <p role="alert">{error}</p>}

          <Card>
            <h3>Пошаговое приготовление</h3>

            <ol className="steps-list">
              {(recipe.steps || []).map((s, i) => (
                <li key={s}>
                  <span>{i + 1}</span>

                  <div>
                    <strong>
                      {[
                        'Подготовка основы',
                        'Замес теста',
                        'Формирование',
                        'Запекание / Обжарка'
                      ][i] || `Шаг ${i + 1}`}
                    </strong>

                    <p>{s}</p>
                  </div>
                </li>
              ))}
            </ol>
          </Card>
        </div>
      </div>
    </div>
  )
}
