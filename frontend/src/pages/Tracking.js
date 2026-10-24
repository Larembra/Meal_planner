import React, { useEffect, useMemo, useState } from "react";
import { Card } from "../components/UI";
import { deleteDiaryEntry, getDiary } from "../api";

export default function Tracking() {
  const [entries, setEntries] = useState([]);
  const [error, setError] = useState("");
  useEffect(() => {
    getDiary().then(setEntries).catch(err => setError(err.message));
  }, []);
  const completed = entries.filter(entry => entry.completed);
  const calories = useMemo(() => completed.reduce((sum, entry) => sum + Number(entry.calories || 0), 0), [completed]);
  const days = new Set(completed.map(entry => entry.entry_date)).size;
  const remove = async id => {
    try {
      await deleteDiaryEntry(id);
      setEntries(previous => previous.filter(entry => entry.id !== id));
    } catch (err) {
      setError(err.message);
    }
  };
  const slotLabels = {
    breakfast: 'Завтрак',
    second_breakfast: '2-й завтрак',
    lunch: 'Обед',
    snack: 'Полдник',
    dinner: 'Ужин',
  };

  return (
    <div className="container">
      <div className="page-title">
        <div>
          <h1>Дневник питания и трекинг</h1>
          <p>
            Следите за прогрессом соблюдения планов КБЖУ в автоматическом режиме
          </p>
        </div>
        <span className="streak">Выполнено приёмов: {completed.length}</span>
      </div>
      <div className="tracking-grid">
        <Card>
          <h3>Ваш прогресс</h3>
          <p>Отмечено дней: <strong>{days}</strong></p>
          <p>Съедено калорий: <strong>{calories.toLocaleString("ru-RU")} ккал</strong></p>
        </Card>
        <Card>
          <h3>Записей в дневнике</h3>
          <p><strong>{entries.length}</strong> приёмов пищи из вашего рациона</p>
        </Card>
        <Card className="full">
          <h3>Выполненные приемы пищи</h3>
          {error && <p role="alert">{error}</p>}
          {!entries.length && <p className="muted" style={{ margin: "8px 0" }}>Записей пока нет. Отметьте блюдо как съеденное в разделе «Мой рацион».</p>}
          {entries.map(entry => (
            <div className="log-row" key={entry.id}>
              <span className={`log-badge ${entry.completed ? "done" : ""}`}>{entry.completed ? "✓" : "○"}</span>
              <div className="log-details">
                <strong>{slotLabels[entry.meal_type] || entry.meal_type}</strong>
                <span className="log-meta">· {entry.entry_date} · {entry.calories} ккал</span>
              </div>
              <button type="button" className="tracking-remove" onClick={() => remove(entry.id)}>Удалить</button>
            </div>
          ))}
        </Card>
      </div>
    </div>
  );
}
