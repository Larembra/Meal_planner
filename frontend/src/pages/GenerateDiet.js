import React, { useState } from "react";
import { Button, Card } from "../components/UI";
import { generateRation } from "../api";

export default function GenerateDiet() {
  const [done, setDone] = useState(false);
  const [period, setPeriod] = useState(7);
  const [tags, setTags] = useState([]);
  const [error, setError] = useState("");
  const generate = async () => {
    try { await generateRation(period, tags); setDone(true); }
    catch (err) { setError(err.message); }
  };
  return (
    <div className="container narrow">
      <div className="page-title">
        <div>
          <h1>Настройка генерации рациона</h1>
          <p>
            ИИ сформирует пошаговое меню с рецептами, опираясь на параметры
            вашего профиля
          </p>
        </div>
      </div>
      <Card>
        <label>
          Период планирования
          <div className="segmented">
            {[1, 3, 7].map(value => <button type="button" key={value}
              className={period === value ? "selected" : ""} onClick={() => setPeriod(value)}>
              {value} {value === 1 ? "день" : "дня"}
            </button>)}
          </div>
        </label>
        <label>
          Дополнительные пожелания к рациону
          <textarea placeholder="Например: Хочу больше сезонных фруктов, или меню для пикника на выходных..." />
        </label>
        <div className="chips">
          {["Быстро готовить", "Недорого", "Больше белка", "Без молочных продуктов", "Минимум мытья посуды"].map(tag =>
            <button type="button" key={tag} className={tags.includes(tag) ? "selected" : ""}
              onClick={() => setTags(v => v.includes(tag) ? v.filter(x => x !== tag) : [...v, tag])}>{tag}</button>)}
        </div>
        {done && (
          <div className="success">
            Рацион успешно сгенерирован! Меню сохранено и добавлено в календарь.
          </div>
        )}
        {error && <p role="alert">{error}</p>}
        <Button onClick={generate}>
          💫 Сгенерировать рацион питания
        </Button>
      </Card>
      <Card className="warning">
        <strong>Превышен бюджет</strong>
        <p>
          Выбранные ограничения не укладываются в 800 рублей. Попробуйте поднять
          лимит или убрать тег «Недорого».
        </p>
      </Card>
    </div>
  );
}
