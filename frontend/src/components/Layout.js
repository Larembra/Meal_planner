import React, { useEffect, useState } from "react";
import { clearSession, getProfile } from "../api";
import ConsultationBar from "./ConsultationBar";


const nav = [
  ["/", "Главная"],
  ["/diet/week", "Мой рацион"],
  ["/recipes", "Рецепты"],
  ["/shopping", "Покупки"],
  ["/tracking", "Трекинг"],
  ["/profile", "Профиль"],
];

export default function Layout({ children }) {
  const path = window.location.pathname;
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem("meal_planner_user")) || null; } catch { return null; }
  });
  useEffect(() => {
    if (localStorage.getItem("meal_planner_access_token")) {
      getProfile().then(next => {
        setUser(next);
        localStorage.setItem("meal_planner_user", JSON.stringify(next));
      }).catch(() => {});
    }
  }, []);
  const name = user?.name || "гость";
  const logout = () => {
    clearSession();
    setUser(null);
    window.location.href = "/login";
  };
  return (
    <div className="app-shell">
      <header className="header">
        <a href="/" className="brand">
          <strong>Витя, где ням-ням?</strong>
          <span>AI РАЦИОН</span>
        </a>
        {user && <nav>
          {nav.map(([href, label]) => (
            <a
              key={href}
              className={
                path === href ||
                (href === "/recipes" && path.startsWith("/recipes"))
                  ? "active"
                  : ""
              }
              href={href}
            >
              {label}
            </a>
          ))}
        </nav>}
        <div className="header-user">
          {user ? <>
            <span>Привет, {name}!</span>
            <details>
              <summary className="avatar" title="Меню аккаунта">{name.charAt(0).toUpperCase()}</summary>
              <a
                href="http://127.0.0.1:8000/docs"
                target="_blank"
                rel="noreferrer"
                style={{ display: "block", padding: "8px 12px", textDecoration: "none", color: "inherit", fontSize: "14px", borderBottom: "1px solid var(--border, #eee)" }}
              >
                Swagger API ↗
              </a>
              <button type="button" onClick={logout}>Выйти из аккаунта</button>
            </details>
          </> : <a href="/login">Войти</a>}
        </div>
      </header>
      <ConsultationBar />
      <main>{children}</main>
    </div>
  );
}
