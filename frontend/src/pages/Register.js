import React, { useState } from "react";
import { Button } from "../components/UI";
import { register } from "../api";

export default function Register() {
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const update = event => setForm({ ...form, [event.target.name]: event.target.value });
  const submit = async event => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(form);
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
          onSubmit={submit}
        >
          <h2>Создать аккаунт</h2>
          <p>Заполните форму для начала вашего пути к здоровой жизни</p>
          <label>
            Ваше имя
            <input name="name" value={form.name} onChange={update} required />
          </label>
          <label>
            Электронная почта
            <input name="email" value={form.email} onChange={update} type="email" required />
          </label>
          <label>
            Пароль
            <input name="password" value={form.password} onChange={update} type="password" minLength="8" required />
          </label>
          {error && <p role="alert">{error}</p>}
          <Button type="submit" disabled={loading}>{loading ? "Создаём..." : "Зарегистрироваться"}</Button>
          <small>
            Уже есть аккаунт? <a href="/login">Войти</a>
          </small>
        </form>
      </div>
    </div>
  );
}
