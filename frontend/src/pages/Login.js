import React from "react";
import { Button } from "../components/UI";

export default function Login() {
  return (
    <div className="auth-page">
      <div className="auth-brand">
        <a href="/" className="brand">
          <strong>Витя, где ням-ням?</strong>
          <span>AI РАЦИОН</span>
        </a>
      </div>
      <div className="auth-center">
        <form
          className="auth-card"
          onSubmit={(e) => {
            e.preventDefault();
            window.location.href = '/';
          }}
        >
          <span className="eyebrow">AI Рацион</span>
          <h1>Рады возвращению!</h1>
          <p>Введите ваши данные для входа в сервис планирования</p>
          <label>
            Электронная почта
            <input defaultValue="vitya@example.com" type="email" />
          </label>
          <label>
            Пароль
            <input defaultValue="12345678" type="password" />
          </label>
          <Button type="submit">Войти в личный кабинет</Button>
          <small>
            Ещё нет профиля? <a href="/register">Зарегистрироваться</a>
          </small>
        </form>
      </div>
    </div>
  );
}
