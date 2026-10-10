import React, { useEffect, useMemo, useState } from "react";
import { Button, Card } from "../components/UI";
import {
  addShoppingItem,
  deleteAllShoppingItems,
  deleteShoppingItem,
  getShoppingItems,
  updateShoppingItem,
} from "../api";

const formatPrice = value => `${Number(value || 0).toLocaleString("ru-RU")} ₽`;
const formatQuantity = value => Number(value || 0).toLocaleString("ru-RU", { maximumFractionDigits: 2 });

export default function Shopping() {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState({ name: "", quantity: "", price: "", category: "other" });
  const [error, setError] = useState("");

  useEffect(() => {
    getShoppingItems().then(setItems).catch(err => setError(err.message));
  }, []);

  const total = useMemo(() => items.reduce((sum, item) => sum + Number(item.price || 0), 0), [items]);
  const groups = useMemo(() => items.reduce((result, item) => {
    const category = item.category || "other";
    if (!result[category]) result[category] = [];
    result[category].push(item);
    return result;
  }, {}), [items]);

  const add = async () => {
    if (!form.name.trim()) return;
    setError("");
    try {
      const item = await addShoppingItem({
        name: form.name.trim(),
        quantity: Number(form.quantity) || 1,
        price: Number(form.price) || 0,
        category: form.category,
      });
      setItems(previous => {
        const existing = previous.find(value => value.id === item.id);
        return existing
          ? previous.map(value => value.id === item.id ? item : value)
          : [...previous, item];
      });
      setForm({ name: "", quantity: "", price: "", category: "other" });
    } catch (err) {
      setError(err.message);
    }
  };

  const toggle = async item => {
    try {
      const updated = await updateShoppingItem(item.id, { is_purchased: !item.is_purchased });
      setItems(previous => previous.map(value => value.id === updated.id ? updated : value));
    } catch (err) {
      setError(err.message);
    }
  };

  const remove = async id => {
    try {
      await deleteShoppingItem(id);
      setItems(previous => previous.filter(item => item.id !== id));
    } catch (err) {
      setError(err.message);
    }
  };

  const removeAll = async () => {
    if (!items.length || !window.confirm("Удалить все товары из списка?")) return;
    try {
      await deleteAllShoppingItems();
      setItems([]);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="container">
      <div className="page-title">
        <div>
          <h1>Мой список покупок</h1>
          <p>Список хранится в вашей базе данных.</p>
        </div>
        <span className="budget">~ {formatPrice(total)}</span>
      </div>
      <div className="shopping-top">
        <input value={form.name} onChange={event => setForm({ ...form, name: event.target.value })} placeholder="Название товара" />
        <input value={form.quantity} onChange={event => setForm({ ...form, quantity: event.target.value })} placeholder="Количество" />
        <input type="number" min="0" value={form.price} onChange={event => setForm({ ...form, price: event.target.value })} placeholder="Цена, ₽" />
        <select value={form.category} onChange={event => setForm({ ...form, category: event.target.value })}>
          <option value="🥩 Мясо и рыба">Мясо и рыба</option>
          <option value="🥬 Бакалея и овощи">Бакалея и овощи</option>
          <option value="🥛 Молочные продукты">Молочные продукты</option>
          <option value="🍎 Фрукты">Фрукты</option>
          <option value="other">Другое</option>
        </select>
        <Button onClick={add}>Добавить</Button>
        <Button variant="secondary" onClick={removeAll} disabled={!items.length}>Удалить все</Button>
      </div>
      {error && <p role="alert">{error}</p>}
      <div className="shopping-grid">
        {Object.entries(groups).map(([category, categoryItems]) => (
          <Card key={category}>
            <h3>{category}</h3>
            {categoryItems.map(item => (
              <div className={item.is_purchased ? "check done" : "check"} key={item.id}>
                <input type="checkbox" checked={item.is_purchased} onChange={() => toggle(item)} />
                <span>{item.name}</span>
                <strong>{formatQuantity(item.quantity)} {item.unit}</strong>
                <em>{formatPrice(item.price)}</em>
                <button type="button" className="shopping-remove" onClick={() => remove(item.id)}>Удалить</button>
              </div>
            ))}
          </Card>
        ))}
        {!items.length && <Card><p>Список пока пуст. Добавьте товар или ингредиенты из рецепта.</p></Card>}
      </div>
    </div>
  );
}
