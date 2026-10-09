import React, { useEffect, useState } from "react";
import { Button, Card } from "../components/UI";
import { getProfile, updateProfile } from "../api";

const goalOptions = [
  { value: "maintain", label: "Поддерживать форму", calories: 1800 },
  { value: "lose_weight", label: "Сбросить вес", calories: 1400 },
  { value: "gain_weight", label: "Набрать массу", calories: 2200 },
];

const dietOptions = [
  { value: "omnivore", label: "Всеядный" },
  { value: "vegetarian", label: "Вегетарианство" },
  { value: "vegan", label: "Веганство" },
  { value: "pescatarian", label: "Пескетарианство" },
];

function normalizeGoal(value) {
  return ({
    "Поддерживать форму": "maintain",
    "Сбросить вес": "lose_weight",
    "Набрать массу": "gain_weight",
  })[value] || value || "maintain";
}

function normalizeDiet(value) {
  return ({
    "Всеядный": "omnivore",
    "Вегетарианство": "vegetarian",
    "Веганство": "vegan",
    "Пескетарианство": "pescatarian",
  })[value] || value || "omnivore";
}

export default function Profile() {
  const [user, setUser] = useState(null);
  const [goal, setGoal] = useState("maintain");
  const [meals, setMeals] = useState("3");
  const [diet, setDiet] = useState("omnivore");
  const [exclusions, setExclusions] = useState("");
  const [budget, setBudget] = useState("");
  const [cookingTime, setCookingTime] = useState("");
  const [preferences, setPreferences] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    getProfile().then(profile => {
      const savedPreferences = profile.preferences || {};
      setUser(profile);
      setGoal(normalizeGoal(profile.goal));
      setMeals(String(savedPreferences.meals_per_day || 3));
      setDiet(normalizeDiet(savedPreferences.diet));
      setExclusions((profile.allergies || []).join(", "));
      setBudget(savedPreferences.budget ?? "");
      setCookingTime(profile.cooking_time_minutes || "");
      setPreferences(savedPreferences.text || "");
    }).catch(err => setMessage(err.message));
  }, []);

  const save = async () => {
    try {
      const next = await updateProfile({
        name: user?.name,
        goal,
        allergies: exclusions.split(",").map(item => item.trim()).filter(Boolean),
        preferences: {
          diet,
          meals_per_day: Number(meals),
          budget: Number(budget) || null,
          text: preferences,
        },
        cooking_time_minutes: Number(cookingTime) || null,
      });
      setUser(next);
      setMessage("Изменения сохранены");
    } catch (err) {
      setMessage(err.message);
    }
  };

  const selectedGoal = goalOptions.find(option => option.value === goal) || goalOptions[0];

  return (
    <div className="container">
      <PageHeader role={user?.role || "client"} />
      <div className="profile-grid profile-grid-settings">
        <Card>
          <h2>🎯 Цель и режим питания</h2>
          <p className="profile-hint">Выберите ориентир по калорийности и удобный распорядок дня.</p>
          <div className="profile-goals">
            {goalOptions.map(option => (
              <button
                type="button"
                key={option.value}
                className={`profile-goal-card${goal === option.value ? " selected" : ""}`}
                onClick={() => setGoal(option.value)}
                aria-pressed={goal === option.value}
              >
                <span>{option.label}</span>
                <strong>≈ {option.calories.toLocaleString("ru-RU")} ккал/день</strong>
              </button>
            ))}
          </div>
          <label>
            Количество приёмов пищи в день
            <select value={meals} onChange={event => setMeals(event.target.value)}>
              {[3, 4, 5].map(value => <option key={value} value={value}>{value} {value === 5 ? "приёмов" : "приёма"}</option>)}
            </select>
          </label>
          <div className="profile-summary">
            <span>Ваш ориентир</span>
            <strong>{selectedGoal.label} · около {selectedGoal.calories.toLocaleString("ru-RU")} ккал в день</strong>
          </div>
        </Card>

        <Card>
          <h2>🥗 Ваши предпочтения</h2>
          <p className="profile-hint">Эти настройки помогут подобрать подходящие блюда и рецепты.</p>
          <label>
            Тип питания
            <select value={diet} onChange={event => setDiet(event.target.value)}>
              {dietOptions.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </label>
          <label>
            Исключить аллергены и продукты
            <input value={exclusions} onChange={event => setExclusions(event.target.value)} placeholder="Например: арахис, молоко" />
          </label>
          <div className="form-grid">
            <label>
              Бюджет на день, руб.
              <input type="number" min="0" value={budget} onChange={event => setBudget(event.target.value)} placeholder="Без ограничения" />
            </label>
            <label>
              Максимум на готовку, мин.
              <input type="number" min="1" value={cookingTime} onChange={event => setCookingTime(event.target.value)} placeholder="Без ограничения" />
            </label>
          </div>
          <label>
            Вкусовые предпочтения
            <textarea value={preferences} onChange={event => setPreferences(event.target.value)} placeholder="Например: люблю рыбу, острые специи и свежие овощи" />
          </label>
        </Card>
      </div>
      <div className="right-actions">
        <Button onClick={save}>Сохранить изменения</Button>
        {message && <p role="status">{message}</p>}
      </div>
    </div>
  );
}

function PageHeader({ role }) {
  return (
    <div className="page-title">
      <div>
        <h1>Настройки рациона</h1>
        <p>Выберите цель, режим питания и ограничения для персонального меню.</p>
      </div>
      <span className="role-badge">{role}</span>
    </div>
  );
}
