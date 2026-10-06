import React from "react";
import { Button } from "../components/UI";

export default function Register() {
  return (
    <div className="auth-page">
      <div className="auth-brand">
        <a href="/" className="brand">
          <strong>Витя, где ням-ням?</strong>
          <span>AI РАЦИОН</span>
        </a>
      </div>
      <div className="auth-grid">
        <div className="auth-intro">
          <span className="eyebrow">AI Рацион</span>
          <h1>Начните питаться вкусно и осознанно уже сегодня</h1>
          <p>Персональные подборки меню от искусственного интеллекта</p>
          <p>Учет аллергий, непереносимостей и бюджета</p>
          <p>Экономия времени на планировании и покупках до 5 часов в неделю</p>
        </div>
        <form
          className="auth-card"
          onSubmit={(e) => {
            e.preventDefault();
            window.location.href = '/';
          }}
        >
          <h2>Создать аккаунт</h2>
          <p>Заполните форму для начала вашего пути к здоровой жизни</p>
          <label>
            Ваше имя
            <input defaultValue="Иван Иванов" />
          </label>
          <label>
            Электронная почта
            <input defaultValue="vitya@example.com" type="email" />
          </label>
          <label>
            Пароль
            <input defaultValue="12345678" type="password" />
          </label>
          <Button type="submit">Зарегистрироваться</Button>
          <small>
            Уже есть аккаунт? <a href="/login">Войти</a>
          </small>
        </form>
      </div>
    </div>
  );
}
