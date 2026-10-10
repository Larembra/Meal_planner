import React, { useEffect, useState } from "react";
import { Button, Card } from "../components/UI";
import { addDiaryEntry, deleteDiaryEntry, getDiary } from "../api";

export default function Tracking() {
  const [entries, setEntries] = useState([]);
  const [error, setError] = useState("");
  const load = () => getDiary().then(setEntries).catch(err => setError(err.message));
  useEffect(load, []);
  const toggle = async entry => {
    try { const updated = await addDiaryEntry({ entry_date: entry.entry_date, meal_type: entry.meal_type, meal_id: entry.meal_id, completed: !entry.completed }); setEntries(values => values.map(value => value.id === updated.id ? updated : value)); }
    catch (err) { setError(err.message); }
  };
  const remove = async id => { await deleteDiaryEntry(id); setEntries(values => values.filter(value => value.id !== id)); };
  return <div className="container">
    <div className="page-title"><div><h1>Дневник питания и трекинг</h1><p>Отмечайте выполненные приёмы пищи в текущем рационе.</p></div></div>
    {error && <p role="alert">{error}</p>}
    <Card><h3>Приёмы пищи</h3>{entries.map(entry => <div className="log-row" key={entry.id}>
      <input type="checkbox" checked={entry.completed} onChange={() => toggle(entry)} />
      <div>{entry.meal_type} · {entry.calories} ккал<br /><small>{entry.entry_date}</small></div>
      <Button variant="secondary" onClick={() => remove(entry.id)}>Удалить</Button>
    </div>)}{!entries.length && <p>В текущем рационе пока нет отмечаемых блюд.</p>}</Card>
  </div>;
}
