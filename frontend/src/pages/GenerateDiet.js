import React, { useEffect, useState } from "react";
import { Button, Card } from "../components/UI";
import { generateRation, getProfile } from "../api";

const QUICK_EXCLUSIONS = [
  "Без яиц",
  "Без молока",
  "Без рыбы",
  "Без орехов",
  "Без глютена",
];

export default function GenerateDiet() {
  const [profile, setProfile] = useState(null);
  const [done, setDone] = useState(false);
  const [period, setPeriod] = useState(7);
  const [extraRequest, setExtraRequest] = useState("");
  const [selectedTags, setSelectedTags] = useState([]);
  const [model, setModel] = useState("gemini-3.5-flash-lite");
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getProfile()
      .then(p => {
        setProfile(p);
        if (p?.allergies && p.allergies.length > 0) {
          const preselected = [];
          for (const a of p.allergies) {
            const lower = a.toLowerCase();
            if (lower.includes("яйц") || lower.includes("яиц")) preselected.push("Без яиц");
            else if (lower.includes("молок") || lower.includes("лактоз")) preselected.push("Без молока");
            else if (lower.includes("рыб")) preselected.push("Без рыбы");
            else if (lower.includes("орех")) preselected.push("Без орехов");
            else if (lower.includes("глютен")) preselected.push("Без глютена");
          }
          if (preselected.length > 0) {
            setSelectedTags(prev => [...new Set([...prev, ...preselected])]);
          }
        }
      })
      .catch(() => {});
  }, []);

  const toggleTag = (tag) => {
    setSelectedTags(prev =>
      prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]
    );
  };

  const generate = async () => {
    setGenerating(true);
    setError("");
    setDone(false);
    try {
      await generateRation(period, selectedTags, extraRequest, model);
      setDone(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setGenerating(false);
    }
  };

  const goalName = {
    maintain: "Поддерживать форму",
    lose_weight: "Сбросить вес",
    gain_weight: "Набрать массу",
  }[profile?.goal] || profile?.goal || "Поддерживать форму";

  const profileAllergies = profile?.allergies || [];

  return (
    <div className="container narrow">
      <div className="page-title">
        <div>
          <h1>Настройка генерации рациона</h1>
          <p>
            ИИ сформирует пошаговое меню с рецептами без повторов, строго соблюдая ваши ограничения и аллергии
          </p>
        </div>
      </div>

      <Card>
        {profile && (
          <div style={{
            background: "var(--light, #f8fbf9)",
            border: "1px solid var(--border, #e2ece6)",
            borderRadius: "12px",
            padding: "14px 18px",
            marginBottom: "20px",
            fontSize: "14px",
            lineHeight: "1.5"
          }}>
            <div>
              <strong>Цель из профиля:</strong> {goalName}
            </div>
            <div>
              <strong>Аллергии из профиля:</strong>{" "}
              {profileAllergies.length > 0 ? (
                <span style={{ color: "#c2410c", fontWeight: "600" }}>
                  {profileAllergies.join(", ")}
                </span>
              ) : (
                <span style={{ color: "var(--muted)" }}>не указаны в профиле</span>
              )}
            </div>
          </div>
        )}

        <label>
          Период планирования
          <div className="segmented">
            {[1, 3, 7].map(value => (
              <button
                type="button"
                key={value}
                className={period === value ? "selected" : ""}
                onClick={() => setPeriod(value)}
              >
                {value} {value === 1 ? "день" : value < 5 ? "дня" : "дней"}
              </button>
            ))}
          </div>
        </label>

        <label>
          Исключить из рациона (аллергии и запреты)
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginTop: "8px", marginBottom: "14px" }}>
            {QUICK_EXCLUSIONS.map(tag => {
              const active = selectedTags.includes(tag);
              return (
                <button
                  type="button"
                  key={tag}
                  onClick={() => toggleTag(tag)}
                  style={{
                    border: active ? "1.5px solid var(--green, #10b981)" : "1px solid var(--border, #d1d5db)",
                    background: active ? "rgba(16, 185, 129, 0.12)" : "#fff",
                    color: active ? "var(--green, #059669)" : "var(--dark, #374151)",
                    borderRadius: "20px",
                    padding: "6px 14px",
                    fontSize: "13px",
                    fontWeight: active ? "600" : "400",
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                  }}
                >
                  {tag} {active && "✓"}
                </button>
              );
            })}
          </div>
        </label>

        <label>
          Дополнительные пожелания к рациону
          <textarea
            value={extraRequest}
            onChange={event => setExtraRequest(event.target.value)}
            placeholder="Например: аллергия на яйца, больше сезонных фруктов, простые блюда..."
          />
        </label>

        <label>
          Модель генерации
          <select value={model} onChange={event => setModel(event.target.value)}>
            <option value="gemini-3.5-flash-lite">Google Gemini 3.5 Flash Lite (быстрая, рекомендуется)</option>
            <option value="gemini-3.8-flash">Google Gemini 3.8 Flash</option>
          </select>
        </label>

        {done && (
          <div className="success" style={{ marginTop: "16px" }}>
            Рацион успешно сгенерирован без дубликатов с учётом всех аллергий!
            <p><a href="/diet/week">Открыть мой рацион →</a></p>
          </div>
        )}

        {error && <p role="alert" style={{ color: "#ef4444", marginTop: "12px" }}>{error}</p>}

        <Button onClick={generate} disabled={generating} style={{ marginTop: "18px" }}>
          {generating ? "Формируем план питания..." : "Сгенерировать рацион питания"}
        </Button>
      </Card>
    </div>
  );
}
