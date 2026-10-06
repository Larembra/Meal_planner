import React from "react";

const nav = [
  ["/", "Главная"],
  ["/diet/today", "Мой рацион"],
  ["/recipes", "Рецепты"],
  ["/shopping", "Покупки"],
  ["/tracking", "Трекинг"],
  ["/profile", "Профиль"],
];

export default function Layout({ children }) {
  const path = window.location.pathname;
  return (
    <div className="app-shell">
      <header className="header">
        <a href="/" className="brand">
          <strong>Витя, где ням-ням?</strong>
          <span>AI РАЦИОН</span>
        </a>
        <nav>
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
        </nav>
        <div className="header-user">
          <span>Привет, Константин!</span>
          <div className="avatar">К</div>
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}
