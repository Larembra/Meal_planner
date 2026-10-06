import React, { useMemo, useState } from "react";
import { Button, Card } from "../components/UI";
import { shoppingGroups, sumIngredientPrices } from "../data/mockData";

const formatPrice = value =>
  `${Number(value || 0).toLocaleString("ru-RU")} ₽`;

export default function Shopping() {
  const [checked, setChecked] = useState([]);
  const groups = shoppingGroups;
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
  const toggle = (id) =>
    setChecked((v) => (v.includes(id) ? v.filter((i) => i !== id) : [...v, id]));

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
        <input placeholder="Добавить свой продукт (например: Сыр 200г)..." />
        <Button>Добавить</Button>
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
              </label>
            ))}
          </Card>
        ))}
      </div>
    </div>
  );
}
