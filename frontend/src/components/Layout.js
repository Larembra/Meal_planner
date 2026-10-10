import React, { useEffect, useState } from "react";
import { clearSession, getProfile } from "../api";

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
              <button type="button" onClick={logout}>Выйти из аккаунта</button>
            </details>
          </> : <a href="/login">Войти</a>}
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}
