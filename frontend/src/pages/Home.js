import React from "react";
import { Button, Card, ImageBox } from "../components/UI";

export function Home() {
  const isLoggedIn = Boolean(localStorage.getItem("meal_planner_access_token"));
  const steps = [
    [
      "01",
      "Постановка цели",
      "Укажите ваши базовые параметры, активность и желаемый результат (похудение, масса или баланс).",
    ],
    [
      "02",
      "Индивидуальные пожелания",
      "Исключите аллергены, выберите тип диеты, укажите личный бюджет и планируемое время у плиты.",
    ],
    [
      "03",
      "Генерация рациона",
      "ИИ подберет сбалансированное меню на день, 3 дня или неделю с пошаговыми простыми рецептами.",
    ],
    [
      "04",
      "Умные покупки",
      "Получите готовый список необходимых продуктов, разбитый по категориям для быстрого похода в магазин.",
    ],
  ];
  return (
    <div className="container home">
      <section className="hero">
        <div className="hero-copy">
          <span className="eyebrow">🥦 Твой умный помощник в питании</span>
          <h1>
            Персональный рацион
            <br />
            без лишнего стресса
          </h1>
          <p>
            «Витя, где ням-ням?» - это умная система планирования меню, которая
            учитывает ваши вкусы, бюджет, цели и время на готовку. Доверьте
            планирование ИИ.
          </p>
          <div className="actions">
            <Button href={isLoggedIn ? "/diet/generate" : "/login"}>
              {isLoggedIn ? "Создать рацион" : "Войти и создать рацион"}
            </Button>
            {!isLoggedIn && <Button href="/login" variant="secondary">Войти в личный кабинет</Button>}
          </div>
        </div>
        <ImageBox src="/static/vitya_nyam_nyam.jpg" className="hero-image" />
      </section>
      <section className="how">
        <span className="eyebrow">Простой процесс</span>
        <h2>Как это работает?</h2>
        <div className="steps">
          {steps.map(([num, title, text]) => (
            <Card key={num}>
              <span className="step-num">{num}</span>
              <h3>{title}</h3>
              <p>{text}</p>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
