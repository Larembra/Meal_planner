import React from 'react'
import { Button, Card, ImageBox } from '../components/UI'
import { weeklyMeals } from '../data/mockData'

export default function WeeklyDiet() {
  const openRecipe = id => {
    window.location.href = `/recipes/${id}`
  }

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
          <h1>Мой рацион на неделю</h1>
          <p>Сбалансированное меню, оптимизированное ИИ под твои параметры</p>
        </div>

        <div className="actions">
          <Button href="/diet/generate">
            💫 Сгенерировать заново
          </Button>

          <Button href="/profile" variant="secondary">
            ⚙️ Изменить параметры
          </Button>
        </div>
      </div>

      <div className="calendar">
        {['Пн 1', 'Вт 2', 'Ср 3', 'Чт 4', 'Пт 5', 'Сб 6', 'Вс 7'].map((d, i) => (
          <div className={i === 4 ? 'selected' : ''} key={d}>
            {d}
          </div>
        ))}
      </div>

      <div className="weekly-list">
        {weeklyMeals.map(meal => (
          <Card
            key={meal.type}
            className="weekly-card weekly-card-clickable"
            onClick={() => openRecipe(meal.recipeId)}
            onKeyDown={event => handleCardKeyDown(event, meal.recipeId)}
            role="link"
            tabIndex={0}
          >
            <ImageBox src={meal.image} />

            <div className="weekly-info">
              <div className="muted">
                {meal.type} ⏱ {meal.time} мин
              </div>

              <h3>{meal.title}</h3>

              <p>{meal.description}</p>

              <strong>
                {meal.calories} ккал | {meal.macros}
              </strong>

              <div className="meal-price">{meal.price} ₽</div>
            </div>

            <div className="weekly-actions">
              <Button
                variant="secondary"
                onClick={event => event.stopPropagation()}
              >
                Заменить ИИ 🔄
              </Button>
            </div>
          </Card>
        ))}
      </div>

      <Card className="dark-cta">
        <div>
          <h2>Не устраивает этот план питания?</h2>
          <p>
            ИИ мгновенно перестроит меню с учетом новых продуктов,
            бюджета или ограничений в твоём профиле.
          </p>
        </div>

        <Button href="/diet/generate">Создать рацион</Button>
      </Card>
    </div>
  )
}