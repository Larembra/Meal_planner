import React, { useMemo, useState } from "react";
import { Button, Card } from "../components/UI";
import { shoppingGroups, sumIngredientPrices } from "../data/mockData";

const formatPrice = value =>
  `${Number(value || 0).toLocaleString("ru-RU")} ₽`;

export default function Shopping() {
  const [checked, setChecked] = useState(() => JSON.parse(localStorage.getItem("shopping_checked") || "[]"));
  const [custom, setCustom] = useState(() => JSON.parse(localStorage.getItem("shopping_custom") || "[]"));
  const [newItem, setNewItem] = useState({ name: "", quantity: "", price: "" });
  const groups = useMemo(() => {
    const base = shoppingGroups.map(group => ({ ...group, items: [...group.items] }));
    if (custom.length) base.push({ title: "🛒 Добавлено вами", items: custom });
    return base;
  }, [custom]);
  const allItems = useMemo(
    () => groups.flatMap(group => group.items),
    [groups],
  );
  const totalItems = allItems.length;
  const boughtPercent =
    totalItems === 0 ? 0 : Math.round((checked.length / totalItems) * 100);
  const totalPrice = useMemo(
    () => sumIngredientPrices(allItems),
    [allItems],
  );
  const toggle = (id) => setChecked(v => {
    const next = v.includes(id) ? v.filter(i => i !== id) : [...v, id];
    localStorage.setItem("shopping_checked", JSON.stringify(next));
    return next;
  });
  const addItem = () => {
    const name = newItem.name.trim();
    if (!name) return;
    const item = { id: `custom-${Date.now()}`, name, quantity: newItem.quantity.trim() || "1 шт.", price: Number(newItem.price) || 0 };
    const next = [...custom, item];
    setCustom(next);
    localStorage.setItem("shopping_custom", JSON.stringify(next));
    setNewItem({ name: "", quantity: "", price: "" });
  };
  const removeItem = id => {
    const next = custom.filter(item => item.id !== id);
    setCustom(next);
    localStorage.setItem("shopping_custom", JSON.stringify(next));
    setChecked(items => items.filter(item => item !== id));
  };

  return (
    <div className="container">
      <div className="page-title">
        <div>
          <h1>Мой список покупок</h1>
          <p>
            Автоматический список нужных ингредиентов для выбранного рациона
          </p>
        </div>
        <span className="budget">~ {formatPrice(totalPrice)}</span>
      </div>
      <div className="shopping-top">
        <div>
          Выкупленные продукты <strong>{boughtPercent}%</strong>
        </div>
        <input value={newItem.name} onChange={e => setNewItem(v => ({ ...v, name: e.target.value }))}
          onKeyDown={e => e.key === "Enter" && addItem()}
          placeholder="Название товара" />
        <input value={newItem.quantity} onChange={e => setNewItem(v => ({ ...v, quantity: e.target.value }))}
          placeholder="Количество / комментарий" />
        <input type="number" min="0" value={newItem.price}
          onChange={e => setNewItem(v => ({ ...v, price: e.target.value }))}
          placeholder="Цена, ₽" />
        <Button onClick={addItem}>Добавить</Button>
      </div>
      <div className="shopping-grid">
        {groups.map((group) => (
          <Card key={group.title}>
            <h3>{group.title}</h3>
            {group.items.map(item => (
              <label
                className={checked.includes(item.id) ? "check done" : "check"}
                key={item.id}
              >
                <input
                  type="checkbox"
                  checked={checked.includes(item.id)}
                  onChange={() => toggle(item.id)}
                />
                <span>{item.name}</span>
                <strong>{item.quantity}</strong>
                <em>{formatPrice(item.price)}</em>
                {String(item.id).startsWith("custom-") && <button type="button" onClick={() => removeItem(item.id)}>Удалить</button>}
              </label>
            ))}
          </Card>
        ))}
      </div>
    </div>
  );
}
