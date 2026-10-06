import React, { useState } from "react";
import { Button, Card } from "../components/UI";
import { user } from "../data/mockData";

export default function Profile() {
  const [goal, setGoal] = useState(user.goal);
  const [age, setAge] = useState(user.age);
  const [height, setHeight] = useState(user.height);
  const [weight, setWeight] = useState(user.weight);
  const [activity, setActivity] = useState("moderate");
  const [meals, setMeals] = useState("4");
  const [diet, setDiet] = useState(user.diet);
  const [exclusions, setExclusions] = useState(user.exclusions.join(", "));
  const [budget, setBudget] = useState(user.budget);
  const [cookingTime, setCookingTime] = useState(user.cookingTime);
  const [preferences, setPreferences] = useState(user.preferences);

  return (
    <div className="container">
      <PageHeader role={user.role} />
      <div className="profile-grid">
        <Card>
          <h2>📊 Базовые данные и цели</h2>
          <div className="segmented">
            <button type="button" className={goal === "Поддерживать форму" ? "selected" : ""} onClick={() => setGoal("Поддерживать форму")}>
              Поддерживать форму
            </button>
            <button type="button" className={goal === "Сбросить вес" ? "selected" : ""} onClick={() => setGoal("Сбросить вес")}>
              Сбросить вес
            </button>
            <button type="button" className={goal === "Набрать массу" ? "selected" : ""} onClick={() => setGoal("Набрать массу")}>
              Набрать массу
            </button>
          </div>
          <div className="form-grid">
            <label>
              Возраст, лет
              <input value={age} onChange={(e) => setAge(e.target.value)} />
            </label>
            <label>
              Рост, см
              <input value={height} onChange={(e) => setHeight(e.target.value)} />
            </label>
            <label>
              Вес, кг
              <input value={weight} onChange={(e) => setWeight(e.target.value)} />
            </label>
            <label>
              Уровень активности
              <select value={activity} onChange={(e) => setActivity(e.target.value)}>
                <option value="low">Минимальный</option>
                <option value="moderate">Умеренный (1-3 тренировки/нед)</option>
                <option value="high">Высокий (4-5 тренировок/нед)</option>
              </select>
            </label>
            <label>
              Количество приёмов пищи
              <select value={meals} onChange={(e) => setMeals(e.target.value)}>
                <option value="3">3 раза</option>
                <option value="4">4 раза</option>
                <option value="5">5 раз</option>
              </select>
            </label>
          </div>
          <div className="profile-summary">
            Выбрана цель: <strong>{goal}</strong>
          </div>
        </Card>
        <Card>
          <h2>🍲 Питание, ограничения и у плиты</h2>
          <label>
            Тип питания
            <select value={diet} onChange={(e) => setDiet(e.target.value)}>
              <option>Всеядный</option>
              <option>Вегетарианство</option>
              <option>Веганство</option>
              <option>Кето</option>
              <option>Пескетарианство</option>
            </select>
          </label>
          <label>
            Исключить аллергены и продукты
            <input value={exclusions} onChange={(e) => setExclusions(e.target.value)} />
          </label>
          <div className="form-grid">
            <label>
              Бюджет на день, руб
              <input value={budget} onChange={(e) => setBudget(e.target.value)} />
            </label>
            <label>
              Макс. время готовки, мин
              <input value={cookingTime} onChange={(e) => setCookingTime(e.target.value)} />
            </label>
          </div>
          <label>
            Вкусовые предпочтения
            <textarea value={preferences} onChange={(e) => setPreferences(e.target.value)} />
          </label>
        </Card>
      </div>
      <div className="right-actions">
        <Button>Сохранить изменения</Button>
      </div>
    </div>
  );
}
function PageHeader({ role }) {
  return (
    <div className="page-title">
      <div>
        <h1>Параметры здоровья и предпочтений</h1>
        <p>
          Настройте постоянные характеристики - они станут основой для генерации
          рациона ИИ
        </p>
      </div>
      <span className="role-badge">{role}</span>
    </div>
  );
}
