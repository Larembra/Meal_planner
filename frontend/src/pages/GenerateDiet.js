import React, { useState } from "react";
import { Button, Card } from "../components/UI";
import { generateRation } from "../api";

export default function GenerateDiet() {
  const [done, setDone] = useState(false);
  const [period, setPeriod] = useState(7);
  const [extraRequest, setExtraRequest] = useState("");
  const [model, setModel] = useState("apodex/apodex-1.1-mini:free");
  const [error, setError] = useState("");
  const generate = async () => {
    try { await generateRation(period, [], extraRequest, model); setDone(true); }
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
          <textarea value={extraRequest} onChange={event => setExtraRequest(event.target.value)}
            placeholder="Например: больше сезонных фруктов, простые блюда..." />
        </label>
        <label>
          Модель генерации
          <select value={model} onChange={event => setModel(event.target.value)}>
            <option value="apodex/apodex-1.1-mini:free">Apodex 1.1 Mini (по умолчанию)</option>
            <option value="liquid/lfm-2.5-2.6b:free">Liquid LFM 2.5</option>
            <option value="nvidia/nemotron-3-ultra-550b-a55b:free">NVIDIA Nemotron 3 Ultra</option>
            <option value="openrouter/free">OpenRouter Free (автовыбор)</option>
          </select>
        </label>
        {done && (
          <div className="success">
            Рацион успешно сгенерирован и сохранён.
            <p><a href="/diet/week">Открыть мой рацион</a></p>
          </div>
        )}
        {error && <p role="alert">{error}</p>}
        <Button onClick={generate}>
          💫 Сгенерировать рацион питания
        </Button>
      </Card>

    </div>
  );
}
