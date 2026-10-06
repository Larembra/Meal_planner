import React, { useMemo, useState } from "react";
import { Button, Card, ImageBox } from "../components/UI";
import { recipes, sumIngredientPrices, ingredientCategories } from "../data/mockData";

const emptyIngredient = () => ({
  name: "",
  quantity: "",
  price: "",
  category: ingredientCategories[2],
});

const defaultIngredients = [
  { name: "Куриное филе", quantity: "200 г", price: 180, category: "🥩 Мясо и рыба" },
  { name: "Брокколи", quantity: "150 г", price: 90, category: "🥬 Бакалея и овощи" },
  { name: "Сливки 10%", quantity: "80 мл", price: 35, category: "🥛 Молочные продукты" },
];

export default function RecipeForm({ mode }) {
  const existing = recipes[0];
  const [steps, setSteps] = useState(
    mode === "edit" ? existing.steps : ["", ""],
  );
  const [ingredients, setIngredients] = useState(
    mode === "edit"
      ? existing.ingredients.map(item => ({
          ...item,
          category: item.category || ingredientCategories[2],
        }))
      : defaultIngredients.map(item => ({ ...item })),
  );
  const [image, setImage] = useState(mode === "edit" ? existing.image : "");
  const addStep = () => setSteps([...steps, ""]);
  const updateStep = (i, v) =>
    setSteps(steps.map((x, idx) => (idx === i ? v : x)));
  const removeStep = (i) => setSteps(steps.filter((_, idx) => idx !== i));

  const addIngredient = () => setIngredients([...ingredients, emptyIngredient()]);
  const updateIngredient = (i, field, value) =>
    setIngredients(items =>
      items.map((item, idx) => (idx === i ? { ...item, [field]: value } : item)),
    );
  const removeIngredient = (i) =>
    setIngredients(items => items.filter((_, idx) => idx !== i));

  const recipePrice = useMemo(
    () => sumIngredientPrices(ingredients),
    [ingredients],
  );

  return (
    <div className="container recipe-form">
      <a href="/recipes" className="back">
        ← {mode === "edit" ? "Отмена редактирования" : "Назад к рецептам"}
      </a>
      <div className="page-title">
        <div>
          <h1>{mode === "edit" ? "Редактирование рецепта" : "Новый рецепт"}</h1>
          <p>
            {mode === "edit"
              ? "Вы можете скорректировать КБЖУ, ингредиенты и этапы приготовления рецепта."
              : "Добавь своё любимое блюдо в базу, чтобы Витя мог рассчитывать его в твоём дневном рационе."}
          </p>
        </div>
      </div>
      <div className="form-layout">
        <div>
          <Card>
            <label>
              Название рецепта
              <input
                defaultValue={mode === "edit" ? existing.title : ""}
                placeholder="Введите название (например: Овсяная каша с бананом)"
              />
            </label>
            <div className="ingredient-section">
              <h3>Ингредиенты</h3>
              <div className="ingredient-editor ingredient-editor-head">
                <span>Название</span>
                <span>Количество</span>
                <span>Цена, ₽</span>
                <span>Категория</span>
                <span />
              </div>
              {ingredients.map((item, i) => (
                <div className="ingredient-editor" key={i}>
                  <input
                    value={item.name}
                    onChange={e => updateIngredient(i, "name", e.target.value)}
                    placeholder="Например: Куриное филе"
                  />
                  <input
                    value={item.quantity}
                    onChange={e => updateIngredient(i, "quantity", e.target.value)}
                    placeholder="200 г"
                  />
                  <input
                    type="number"
                    min="0"
                    step="1"
                    value={item.price}
                    onChange={e => updateIngredient(i, "price", e.target.value)}
                    placeholder="0"
                  />
                  <select
                    value={item.category || ingredientCategories[2]}
                    onChange={e => updateIngredient(i, "category", e.target.value)}
                  >
                    {ingredientCategories.map(category => (
                      <option key={category} value={category}>
                        {category}
                      </option>
                    ))}
                  </select>
                  <button type="button" onClick={() => removeIngredient(i)}>
                    Удалить
                  </button>
                </div>
              ))}
              <Button variant="secondary" onClick={addIngredient}>
                Добавить ингредиент
              </Button>
              <div className="recipe-price-total">
                Цена рецепта: <strong>{recipePrice} ₽</strong>
              </div>
            </div>
            <label>
              Фото готового блюда
              <input
                type="file"
                accept="image/png,image/jpeg"
                onChange={e =>
                  e.target.files?.[0] &&
                  setImage(URL.createObjectURL(e.target.files[0]))
                }
              />
            </label>
            <ImageBox src={image} className="form-image" />
            <small>Поддерживаются JPG, PNG до 10 МБ</small>
          </Card>
          <Card>
            <h3>Пищевая ценность (на 100г)</h3>
            <div className="form-grid four">
              <label>
                Калории (ккал)
                <input defaultValue={mode === "edit" ? existing.calories : 0} />
              </label>
              <label>
                Белки (г)
                <input defaultValue={mode === "edit" ? existing.protein : 0} />
              </label>
              <label>
                Жиры (г)
                <input defaultValue={mode === "edit" ? existing.fat : 0} />
              </label>
              <label>
                Углеводы (г)
                <input defaultValue={mode === "edit" ? existing.carbs : 0} />
              </label>
            </div>
          </Card>
        </div>
        <div>
          <Card>
            <h3>Шаги приготовления</h3>
            {steps.map((step, i) => (
              <div className="step-editor" key={i}>
                <span>{i + 1}</span>
                <textarea
                  value={step}
                  onChange={e => updateStep(i, e.target.value)}
                  placeholder="Опишите действия на этом этапе приготовления..."
                />
                <button type="button" onClick={() => removeStep(i)}>
                  Удалить
                </button>
              </div>
            ))}
            <Button variant="secondary" onClick={addStep}>
              Добавить шаг
            </Button>
          </Card>
          <Card>
            <div className="form-grid">
              <label>
                Время приготовления (минут)
                <input
                  defaultValue={mode === "edit" ? existing.time : ""}
                  placeholder="Например: 25"
                />
              </label>
              <label>
                Категория
                <select
                  defaultValue={mode === "edit" ? existing.category : "Ужин"}
                >
                  <option>Завтрак</option>
                  <option>Обед</option>
                  <option>Ужин</option>
                  <option>Перекус</option>
                </select>
              </label>
            </div>
          </Card>
        </div>
      </div>
      <div className="right-actions">
        <Button href="/recipes" variant="secondary">
          Отмена
        </Button>
        <Button href="/recipes">
          {mode === "edit" ? "Сохранить изменения" : "Создать рецепт"}
        </Button>
      </div>
    </div>
  );
}
