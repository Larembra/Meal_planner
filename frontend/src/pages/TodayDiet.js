import React from 'react'
import { Button, Card, ImageBox, ProgressRing } from '../components/UI'
import { dailyMeals, user } from '../data/mockData'

export default function TodayDiet() {
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
          <h1>Твой рацион на сегодня</h1>
          <p>
            Баланс калорий рассчитан с учётом профиля «{user.name}, {user.age} лет»
          </p>
        </div>

        <Button href="/diet/generate">
          ✨ Сгенерировать новый рацион
        </Button>
      </div>

      <Card>
        <div className="progress-head">
          <div>
            <h3>Прогресс дня</h3>
            <p>
              Вы придерживаетесь плана питания на <strong>92%</strong>.
              Обед завершён, впереди легкий перекус и ужин.
            </p>
          </div>

          <div className="rings">
            <ProgressRing value={79} label="Калории" unit="1420 ккал" />
            <ProgressRing value={77} label="Белки" unit="92 г" />
            <ProgressRing value={74} label="Жиры" unit="48 г" />
            <ProgressRing value={86} label="Углеводы" unit="155 г" />
          </div>
        </div>
      </Card>

      <div className="meal-grid">
        {dailyMeals.map(meal => (
          <Card
            key={meal.type}
            className="meal-card-clickable"
            onClick={() => openRecipe(meal.recipeId)}
            onKeyDown={event => handleCardKeyDown(event, meal.recipeId)}
            role="link"
            tabIndex={0}
          >
            <ImageBox src={meal.image} />

            <div className="meal-body">
              <div className="muted">
                {meal.type} ⏱ {meal.time} мин
              </div>

              <h3>{meal.title}</h3>
              <p>{meal.macros}</p>
              <strong>{meal.calories} ккал</strong>
              <div className="meal-price">{meal.price} ₽</div>
            </div>
          </Card>
        ))}
      </div>

      <Card>
        <h2>Прогресс текущей недели</h2>

        <div className="week-bars">
          {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].map((d, i) => (
            <div key={d}>
              <span
                className={i === 4 ? 'bar current' : 'bar'}
                style={{ height: `${35 + i * 8}px` }}
              />
              <small>{d}</small>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}