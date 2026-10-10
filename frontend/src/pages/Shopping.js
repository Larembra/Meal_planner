import React, { useEffect, useMemo, useState } from "react";
import { Button, Card } from "../components/UI";
import { addShoppingItem, deleteAllShoppingItems, deleteShoppingItem, getShoppingItems, updateShoppingItem } from "../api";

const price = value => `${Number(value || 0).toLocaleString("ru-RU")} ₽`;
const quantity = value => Number(value || 0).toLocaleString("ru-RU", {
  maximumFractionDigits: 2,
});

export default function Shopping() {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState({ name: "", quantity: "", price: "", category: "other" });
  const [error, setError] = useState("");
  useEffect(() => { getShoppingItems().then(setItems).catch(err => setError(err.message)); }, []);
  const total = useMemo(() => items.reduce((sum, item) => sum + Number(item.price || 0), 0), [items]);
  const groups = useMemo(() => items.reduce((result, item) => {
    const category = item.category || "other";
    if (!result[category]) result[category] = [];
    result[category].push(item);
    return result;
  }, {}), [items]);
  const add = async () => {
    if (!form.name.trim()) return;
    try {
      const item = await addShoppingItem({ name: form.name, quantity: Number(form.quantity) || 1, price: Number(form.price) || 0, category: form.category });
      setItems(previous => [...previous, item]);
      setForm({ name: "", quantity: "", price: "", category: "other" });
    } catch (err) { setError(err.message); }
  };
  const toggle = async item => {
    const updated = await updateShoppingItem(item.id, { is_purchased: !item.is_purchased });
    setItems(previous => previous.map(value => value.id === updated.id ? updated : value));
  };
  const remove = async id => {
    await deleteShoppingItem(id);
    setItems(previous => previous.filter(item => item.id !== id));
  };
  const removeAll = async () => {
    if (!window.confirm("Удалить все товары из списка?")) return;
    await deleteAllShoppingItems();
    setItems([]);
  };
  return <div className="container">
    <div className="page-title"><div><h1>Мой список покупок</h1><p>Список хранится в вашей базе данных.</p></div><span className="budget">~ {price(total)}</span></div>
    <div className="shopping-top">
      <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Название товара" />
      <input value={form.quantity} onChange={e => setForm({ ...form, quantity: e.target.value })} placeholder="Количество" />
      <input type="number" min="0" value={form.price} onChange={e => setForm({ ...form, price: e.target.value })} placeholder="Цена, ₽" />
      <select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })}>
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
      {Object.entries(groups).map(([category, categoryItems]) => <Card key={category}>
        <h3>{category}</h3>
        {categoryItems.map(item => <div className={item.is_purchased ? "check done" : "check"} key={item.id}>
          <input type="checkbox" checked={item.is_purchased} onChange={() => toggle(item)} />
          <span>{item.name}</span><strong>{quantity(item.quantity)} {item.unit}</strong><em>{price(item.price)}</em>
          <button type="button" onClick={() => remove(item.id)}>Удалить</button>
        </div>)}
      </Card>)}
      {!items.length && <Card><p>Список пока пуст. Добавьте товар или ингредиенты из рецепта.</p></Card>}
    </div>
  </div>;
}
