import React, { useState } from "react";
import { Button } from "../components/UI";
import { login } from "../api";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      window.location.href = "/";
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

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
          onSubmit={submit}
        >
          <span className="eyebrow">AI Рацион</span>
          <h1>Рады возвращению!</h1>
          <p>Введите ваши данные для входа в сервис планирования</p>
          <label>
            Электронная почта
            <input value={email} onChange={e => setEmail(e.target.value)} type="email" required />
          </label>
          <label>
            Пароль
            <input value={password} onChange={e => setPassword(e.target.value)} type="password" required />
          </label>
          {error && <p role="alert">{error}</p>}
          <Button type="submit" disabled={loading}>{loading ? "Входим..." : "Войти в личный кабинет"}</Button>
          <small>
            Ещё нет профиля? <a href="/register">Зарегистрироваться</a>
          </small>
        </form>
      </div>
    </div>
  );
}
