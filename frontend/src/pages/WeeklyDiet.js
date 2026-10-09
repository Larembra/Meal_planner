import React, { useEffect, useMemo, useState } from 'react'
import { Button, Card, ImageBox } from '../components/UI'
import { getRationPlan, getRations } from '../api'

const slotLabels = {
  breakfast: 'Завтрак', second_breakfast: '2-й завтрак', lunch: 'Обед', snack: 'Полдник', dinner: 'Ужин',
}
const dayWord = count => count === 1 ? 'день' : count > 1 && count < 5 ? 'дня' : 'дней'

function parseDate(value) {
  const [year, month, day] = value.split('-').map(Number)
  return new Date(year, month - 1, day)
}

function formatDate(value) {
  const date = parseDate(value)
  return {
    short: new Intl.DateTimeFormat('ru-RU', { weekday: 'short', day: 'numeric', month: 'short' }).format(date),
    long: new Intl.DateTimeFormat('ru-RU', { weekday: 'long', day: 'numeric', month: 'long' }).format(date),
  }
}

export default function WeeklyDiet() {
  const [plan, setPlan] = useState(null)
  const [selectedDate, setSelectedDate] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    async function loadPlan() {
      try {
        const rations = await getRations()
        if (!rations.length) {
          if (!cancelled) setPlan(null)
          return
        }
        const latest = await getRationPlan(rations[0].id)
        if (!cancelled) {
          setPlan(latest)
          const dates = [...new Set(latest.meals.map(meal => meal.date))].sort()
          setSelectedDate(dates[0] || '')
        }
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    loadPlan()
    return () => { cancelled = true }
  }, [])

  const days = useMemo(() => {
    if (!plan) return []
    const grouped = new Map()
    for (const meal of plan.meals) {
      if (!grouped.has(meal.date)) grouped.set(meal.date, [])
      grouped.get(meal.date).push(meal)
    }
    return [...grouped.entries()].sort(([a], [b]) => a.localeCompare(b))
  }, [plan])
  const meals = days.find(([day]) => day === selectedDate)?.[1] || []

  const openRecipe = id => { window.location.href = `/recipes/${id}` }
  const handleCardKeyDown = (event, id) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      openRecipe(id)
    }
  }

  return (
    <div className="container">
      <div className="page-title">
        <div>
          <h1>Мой рацион</h1>
          <p>{plan ? `План на ${days.length} ${dayWord(days.length)}` : 'Ваш персональный план питания'}</p>
        </div>
        <div className="actions">
          <Button href="/diet/generate">💫 Сгенерировать рацион</Button>
          <Button href="/profile" variant="secondary">⚙️ Настройки</Button>
        </div>
      </div>

      {loading && <p role="status">Загружаем рацион…</p>}
      {error && <p role="alert">{error}</p>}
      {!loading && !error && !plan && (
        <Card>
          <h2>Рациона пока нет</h2>
          <p>Создайте рацион, и здесь появятся дни и блюда из вашего плана.</p>
          <Button href="/diet/generate">Создать рацион</Button>
        </Card>
      )}
      {!!days.length && (
        <>
          <nav className="calendar" aria-label="Дни рациона">
            {days.map(([day]) => (
              <button type="button" key={day} className={selectedDate === day ? 'selected' : ''}
                aria-pressed={selectedDate === day} onClick={() => setSelectedDate(day)}>
                {formatDate(day).short}
              </button>
            ))}
          </nav>
          <h2>{formatDate(selectedDate).long}</h2>
          {meals.length ? (
            <div className="weekly-list">
              {meals.map(meal => (
                <Card key={meal.ration_meal_id || meal.id}
                  className="weekly-card weekly-card-clickable"
                  onClick={() => openRecipe(meal.id)}
                  onKeyDown={event => handleCardKeyDown(event, meal.id)}
                  role="link" tabIndex={0}>
                  <ImageBox src={meal.image_url} />
                  <div className="weekly-info">
                    <div className="muted">{slotLabels[meal.meal_type] || meal.meal_type} · {meal.cooking_time} мин</div>
                    <h3>{meal.name}</h3>
                    <p>{meal.description}</p>
                    <strong>{meal.calories} ккал | Б {meal.protein} г · Ж {meal.fat} г · У {meal.carbs} г</strong>
                    <div className="meal-price">{meal.cost} ₽ · {meal.servings} порц.</div>
                  </div>
                </Card>
              ))}
            </div>
          ) : <Card>На этот день блюда не запланированы.</Card>}
        </>
      )}
      {!loading && !error && plan && !days.length && (
        <Card>
          <h2>В рационе пока нет блюд</h2>
          <p>Сгенерируйте план, чтобы здесь появились дни и блюда.</p>
          <Button href="/diet/generate">Создать рацион</Button>
        </Card>
      )}
    </div>
  )
}
