import React, { useState } from "react";
import { consultAssistant } from "../api";

export default function ConsultationBar() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState(null);
  const [error, setError] = useState(null);
  const [isOpen, setIsOpen] = useState(true);

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    const cleanQuery = query.trim();
    if (!cleanQuery) return;

    setLoading(true);
    setError(null);
    setAnswer(null);

    try {
      // Single request to the model, no context is saved
      const res = await consultAssistant(cleanQuery);
      setAnswer(res.answer);
    } catch (err) {
      setError(err.message || "Ошибка при получении консультации");
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setQuery("");
    setAnswer(null);
    setError(null);
  };

  return (
    <div className="consultation-wrapper">
      <div className="container">
        <div className="consultation-card">
          <div className="consultation-header">
            <div className="consultation-title">
              <span className="consultation-icon">⚡</span>
              <strong>ИИ-консультант по питанию</strong>
              <span className="consultation-badge">Экспресс-совет (без контекста)</span>
            </div>
            <button
              type="button"
              className="consultation-toggle-btn"
              onClick={() => setIsOpen(!isOpen)}
              title={isOpen ? "Свернуть строку консультации" : "Развернуть строку консультации"}
            >
              {isOpen ? "Свернуть ▲" : "Задать вопрос ▼"}
            </button>
          </div>

          {isOpen && (
            <div className="consultation-body">
              <form onSubmit={handleSubmit} className="consultation-form">
                <div className="consultation-input-row">
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Задайте вопрос о питании, КБЖУ, рецептах или диетах (например: «Чем заменить яйца в сырниках?»)"
                    disabled={loading}
                    className="consultation-input"
                  />
                  {query && (
                    <button
                      type="button"
                      className="consultation-clear-btn"
                      onClick={handleClear}
                      title="Очистить"
                    >
                      ✕
                    </button>
                  )}
                  <button
                    type="submit"
                    className="consultation-submit-btn"
                    disabled={loading || !query.trim()}
                  >
                    {loading ? "Анализируем..." : "Получить совет"}
                  </button>
                </div>
              </form>

              {error && (
                <div className="consultation-alert consultation-error" role="alert">
                  <div className="alert-content">
                    <span className="alert-icon">⚠️</span>
                    <span>{error}</span>
                  </div>
                  <button type="button" onClick={() => setError(null)} className="alert-close">
                    ✕
                  </button>
                </div>
              )}

              {answer && (
                <div className="consultation-result">
                  <div className="result-header">
                    <span className="result-tag">Сухой совет эксперта:</span>
                    <button type="button" onClick={() => setAnswer(null)} className="alert-close">
                      ✕
                    </button>
                  </div>
                  <div className="result-text">{answer}</div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
