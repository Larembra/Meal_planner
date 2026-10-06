import React from "react";
import { Card, ProgressRing } from "../components/UI";

export default function Tracking() {
  return (
    <div className="container">
      <div className="page-title">
        <div>
          <h1>Дневник питания и трекинг</h1>
          <p>
            Следите за прогрессом соблюдения планов КБЖУ в автоматическом режиме
          </p>
        </div>
        <span className="streak">🔥 12 дней строго по плану!</span>
      </div>
      <div className="tracking-grid">
        <Card>
          <h3>Потребление на сегодня (Пятница)</h3>
          <div className="rings large">
            <ProgressRing
              value={78}
              label="Калории"
              unit="1420 ккал / 1800 ккал"
            />
            <ProgressRing value={76} label="Белки" unit="92г / 120г" />
            <ProgressRing value={73} label="Жиры" unit="48г / 65г" />
            <ProgressRing value={86} label="Углеводы" unit="155г / 180г" />
          </div>
        </Card>
        <Card>
          <h3>Соблюдение КБЖУ за неделю</h3>
          <div className="chart-bars">
            {[72, 82, 68, 88, 78, 56, 42].map((v, i) => (
              <div key={i}>
                <span style={{ height: `${v}%` }}></span>
                <small>{["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][i]}</small>
              </div>
            ))}
          </div>
        </Card>
        <Card className="full">
          <h3>Выполненные приемы пищи</h3>
          {[
            ["Завтрак: Сырники из творога с ягодами", "09:00"],
            ["Обед: Борщ со сметаной и ржаным хлебом", "14:15"],
            ["Перекус: Йогурт греческий с миндалем", "17:00"],
            ["Ужин: Форель на гриле с брокколи", "20:00"],
          ].map(([x, t]) => (
            <div className="log-row" key={x}>
              <span>✓</span>
              <div>{x}</div>
              <time>{t}</time>
            </div>
          ))}
        </Card>
      </div>
    </div>
  );
}
