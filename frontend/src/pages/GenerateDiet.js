import React, { useState } from "react";
import { Button, Card } from "../components/UI";

export default function GenerateDiet() {
  const [done, setDone] = useState(false);
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
            <button>1 день</button>
            <button>3 дня</button>
            <button className="selected">7 дней</button>
          </div>
        </label>
        <label>
          Дополнительные пожелания к рациону
          <textarea placeholder="Например: Хочу больше сезонных фруктов, или меню для пикника на выходных..." />
        </label>
        <div className="chips">
          <button>Быстро готовить</button>
          <button>Недорого</button>
          <button>Больше белка</button>
          <button>Без молочных продуктов</button>
          <button>Минимум мытья посуды</button>
        </div>
        {done && (
          <div className="success">
            Рацион успешно сгенерирован! Меню сохранено и добавлено в календарь.
          </div>
        )}
        <Button onClick={() => setDone(true)}>
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
