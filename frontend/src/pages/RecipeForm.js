import React, { useEffect, useState } from "react";
import { Button, Card, ImageBox } from "../components/UI";
import { ingredientCategories } from "../data/mockData";
import {
  createRecipe,
  getRecipe,
  updateRecipe,
  estimateDishPrice,
  suggestDishImage,
  estimateIngredientsPrice,
  estimateNutrition,
  generateCookingSteps,
  estimateCookingTime,
  generateFullRecipe,
} from "../api";


const emptyIngredient = () => ({
  name: "",
  quantity: "",
  price: "",
  category: ingredientCategories[2],
});

const defaultIngredients = [
  { name: "Куриное филе", quantity: "200 г", price: 360, category: "Мясо и рыба" },
  { name: "Брокколи", quantity: "150 г", price: 165, category: "Бакалея и овощи" },
  { name: "Сливки 10%", quantity: "80 мл", price: 95, category: "Молочные продукты" },
];

export default function RecipeForm({ mode }) {
  const recipeId = new URLSearchParams(window.location.search).get("id");
  const [name, setName] = useState("");
  const [category, setCategory] = useState("Ужин");
  const [time, setTime] = useState(0);
  const [calories, setCalories] = useState(0);
  const [protein, setProtein] = useState(0);
  const [fat, setFat] = useState(0);
  const [carbs, setCarbs] = useState(0);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [steps, setSteps] = useState(["", ""]);
  const [ingredients, setIngredients] = useState(
    defaultIngredients.map(item => ({ ...item })),
  );
  const [image, setImage] = useState("");
  const [price, setPrice] = useState(0);

  // AI Loading & Status States
  const [isPriceEstimating, setIsPriceEstimating] = useState(false);
  const [priceComment, setPriceComment] = useState("");
  const [priceError, setPriceError] = useState("");

  const [isImageLoading, setIsImageLoading] = useState(false);
  const [imageSource, setImageSource] = useState("");
  const [imageError, setImageError] = useState("");

  const [isIngredientsLoading, setIsIngredientsLoading] = useState(false);
  const [ingredientsComment, setIngredientsComment] = useState("");
  const [ingredientsError, setIngredientsError] = useState("");

  const [isNutritionLoading, setIsNutritionLoading] = useState(false);
  const [nutritionComment, setNutritionComment] = useState("");
  const [nutritionError, setNutritionError] = useState("");

  const [isStepsLoading, setIsStepsLoading] = useState(false);
  const [stepsComment, setStepsComment] = useState("");
  const [stepsError, setStepsError] = useState("");

  const [isTimeLoading, setIsTimeLoading] = useState(false);
  const [timeComment, setTimeComment] = useState("");
  const [timeError, setTimeError] = useState("");

  const [isMagicLoading, setIsMagicLoading] = useState(false);
  const [magicComment, setMagicComment] = useState("");
  const [magicError, setMagicError] = useState("");

  useEffect(() => {
    if (mode !== "edit" || !recipeId) return;
    getRecipe(recipeId)
      .then(existing => {
        setName(existing.title || "");
        setCategory(existing.category || "Ужин");
        setTime(existing.time || 0);
        setCalories(existing.calories || 0);
        setProtein(existing.protein || 0);
        setFat(existing.fat || 0);
        setCarbs(existing.carbs || 0);
        setPrice(existing.price || 0);
        setSteps(existing.steps?.length ? existing.steps : ["", ""]);
        setIngredients(
          (existing.ingredients || []).map(item => ({
            ...item,
            category: item.category || ingredientCategories[2],
          })),
        );
        setImage(existing.image || "");
      })
      .catch(err => setError(err.message));
  }, [mode, recipeId]);

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

  // 1. Magic All-In-One Generator
  const handleMagicFillAll = async () => {
    const cleanName = name.trim();
    if (!cleanName) {
      setMagicError("Сначала введите название блюда для автозаполнения");
      return;
    }
    setIsMagicLoading(true);
    setMagicError("");
    setMagicComment("");
    try {
      const res = await generateFullRecipe({
        dish_name: cleanName,
        category,
      });
      if (res.ingredients?.length) {
        setIngredients(
          res.ingredients.map(i => ({
            ...i,
            category: i.category || ingredientCategories[2],
          })),
        );
      }
      if (res.price) setPrice(res.price);
      if (res.calories != null) setCalories(res.calories);
      if (res.protein != null) setProtein(res.protein);
      if (res.fat != null) setFat(res.fat);
      if (res.carbs != null) setCarbs(res.carbs);
      if (res.time != null) setTime(res.time);
      if (res.steps?.length) setSteps(res.steps);
      if (res.image_url) {
        setImage(res.image_url);
        setImageSource("Фото подобрано ИИ");
      }
      setMagicComment("Рецепт полностью сгенерирован и заполнен ИИ!");
    } catch (err) {
      setMagicError(err.message || "Не удалось автоматически сформировать рецепт");
    } finally {
      setIsMagicLoading(false);
    }
  };

  // 2. Ingredients Price Estimation
  const handleAutoIngredientsPrice = async () => {
    const cleanName = name.trim();
    if (!cleanName) {
      setIngredientsError("Сначала укажите название блюда");
      return;
    }
    setIsIngredientsLoading(true);
    setIngredientsError("");
    setIngredientsComment("");
    try {
      const res = await estimateIngredientsPrice({
        dish_name: cleanName,
        ingredients,
      });
      if (res.ingredients?.length) {
        setIngredients(
          res.ingredients.map(i => ({
            ...i,
            category: i.category || ingredientCategories[2],
          })),
        );
      }
      if (res.total_price) {
        setPrice(res.total_price);
      }
      setIngredientsComment(res.comment || "Цены ингредиентов рассчитаны ИИ");
    } catch (err) {
      setIngredientsError(err.message || "Не удалось рассчитать цены ингредиентов");
    } finally {
      setIsIngredientsLoading(false);
    }
  };

  // 3. Nutrition (КБЖУ) Estimation
  const handleAutoNutrition = async () => {
    const cleanName = name.trim();
    if (!cleanName) {
      setNutritionError("Сначала укажите название блюда");
      return;
    }
    setIsNutritionLoading(true);
    setNutritionError("");
    setNutritionComment("");
    try {
      const res = await estimateNutrition({
        dish_name: cleanName,
        ingredients,
      });
      setCalories(res.calories ?? 0);
      setProtein(res.protein ?? 0);
      setFat(res.fat ?? 0);
      setCarbs(res.carbs ?? 0);
      setNutritionComment(res.comment || "КБЖУ рассчитано ИИ");
    } catch (err) {
      setNutritionError(err.message || "Не удалось рассчитать КБЖУ");
    } finally {
      setIsNutritionLoading(false);
    }
  };

  // 4. Cooking Steps Generation
  const handleAutoSteps = async () => {
    const cleanName = name.trim();
    if (!cleanName) {
      setStepsError("Сначала укажите название блюда");
      return;
    }
    setIsStepsLoading(true);
    setStepsError("");
    setStepsComment("");
    try {
      const res = await generateCookingSteps({
        dish_name: cleanName,
        ingredients,
      });
      if (res.steps?.length) {
        setSteps(res.steps);
        setStepsComment(res.comment || "Шаги сформированы ИИ");
      }
    } catch (err) {
      setStepsError(err.message || "Не удалось сгенерировать шаги");
    } finally {
      setIsStepsLoading(false);
    }
  };

  // 5. Cooking Time Estimation
  const handleAutoTime = async () => {
    const cleanName = name.trim();
    if (!cleanName) {
      setTimeError("Сначала укажите название блюда");
      return;
    }
    setIsTimeLoading(true);
    setTimeError("");
    setTimeComment("");
    try {
      const res = await estimateCookingTime({
        dish_name: cleanName,
        steps,
        ingredients,
      });
      setTime(res.cooking_time || 20);
      setTimeComment(res.comment || "Время рассчитано ИИ");
    } catch (err) {
      setTimeError(err.message || "Не удалось рассчитать время");
    } finally {
      setIsTimeLoading(false);
    }
  };

  // 6. Total Dish Price Estimation
  const handleAutoPrice = async () => {
    const cleanName = name.trim();
    if (!cleanName) {
      setPriceError("Сначала укажите название блюда для оценки цены");
      return;
    }
    setIsPriceEstimating(true);
    setPriceError("");
    setPriceComment("");
    try {
      const ingredientNames = ingredients.map(i => i.name).filter(Boolean);
      const res = await estimateDishPrice({
        dish_name: cleanName,
        category,
        ingredients: ingredientNames,
      });
      setPrice(res.price);
      setPriceComment(res.comment || "Цена определена ИИ");
    } catch (err) {
      setPriceError(err.message || "Не удалось оценить стоимость");
    } finally {
      setIsPriceEstimating(false);
    }
  };

  // 7. Image Suggestion (Pinterest / Wikipedia / TheMealDB)
  const handleAutoImage = async () => {
    const cleanName = name.trim();
    if (!cleanName) {
      setImageError("Сначала укажите название блюда для подбора фото");
      return;
    }
    setIsImageLoading(true);
    setImageError("");
    try {
      const res = await suggestDishImage({
        dish_name: cleanName,
        category,
      });
      setImage(res.image_url);
      setImageSource(res.comment || "Фото подобрано ИИ");
    } catch (err) {
      setImageError(err.message || "Не удалось подобрать фото");
    } finally {
      setIsImageLoading(false);
    }
  };

  const save = async () => {
    setError("");
    setSaving(true);
    try {
      const payload = {
        name,
        category,
        time: Number(time) || 0,
        calories: Number(calories) || 0,
        protein: Number(protein) || 0,
        fat: Number(fat) || 0,
        carbs: Number(carbs) || 0,
        price: Number(price) || 0,
        image,
        ingredients,
        steps,
      };
      if (mode === "edit" && recipeId) await updateRecipe(recipeId, payload);
      else await createRecipe(payload);
      window.location.href = "/recipes";
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

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
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="Введите название (например: Омлет с беконом)"
              />
            </label>

            {/* Banner for All-in-one AI Generation */}
            <div className="magic-fill-banner">
              <div className="magic-fill-text">
                <strong>ИИ-ассистент шеф-повара</strong>
                <span>
                  Заполнить все поля (ингредиенты с ценами, КБЖУ, шаги, время и фото) в один клик:
                </span>
              </div>
              <button
                type="button"
                className="magic-fill-btn"
                onClick={handleMagicFillAll}
                disabled={isMagicLoading || !name.trim()}
                title="Автоматически сформировать и заполнить все поля рецепта"
              >
                {isMagicLoading ? "Заполняем рецепт..." : "Заполнить всё через ИИ"}
              </button>
            </div>
            {magicError && (
              <div className="ai-error-message" role="alert">
                {magicError}
              </div>
            )}
            {magicComment && !magicError && (
              <div className="ai-comment-badge" style={{ marginBottom: "14px" }}>
                {magicComment}
              </div>
            )}

            <div className="ingredient-section">
              <div className="section-title-with-ai">
                <h3>Ингредиенты</h3>
                <button
                  type="button"
                  className="ai-action-btn"
                  onClick={handleAutoIngredientsPrice}
                  disabled={isIngredientsLoading || !name.trim()}
                  title="Рассчитать рыночную цену каждого ингредиента в рублях через ИИ"
                >
                  {isIngredientsLoading
                    ? "Считаем цены..."
                    : "Рассчитать цены через AI"}
                </button>
              </div>

              {ingredientsError && (
                <div className="ai-error-message" role="alert">
                  {ingredientsError}
                </div>
              )}
              {ingredientsComment && !ingredientsError && (
                <div className="ai-comment-badge" style={{ marginBottom: "10px" }}>
                  {ingredientsComment}
                </div>
              )}

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
                    placeholder="Например: Бекон с/к"
                  />
                  <input
                    value={item.quantity}
                    onChange={e => updateIngredient(i, "quantity", e.target.value)}
                    placeholder="60 г"
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

              <div className="recipe-price-box">
                <div className="recipe-price-header">
                  <div>
                    <strong>Итоговая стоимость блюда</strong>
                    <span className="recipe-price-sub"> (автоматическая оценка ИИ)</span>
                  </div>
                  <button
                    type="button"
                    className="ai-action-btn"
                    onClick={handleAutoPrice}
                    disabled={isPriceEstimating || !name.trim()}
                    title="Запросить у нейросети среднюю стоимость порции этого блюда"
                  >
                    {isPriceEstimating ? "Оцениваем..." : "Оценить стоимость порции"}
                  </button>
                </div>
                <div className="recipe-price-input-row">
                  <input
                    type="number"
                    min="0"
                    step="1"
                    value={price}
                    onChange={e => setPrice(Number(e.target.value) || 0)}
                    placeholder="0"
                    className="recipe-price-input"
                  />
                  <span className="currency-label">₽</span>
                  {priceComment && (
                    <span className="ai-comment-badge">{priceComment}</span>
                  )}
                </div>
                {priceError && (
                  <div className="ai-error-message" role="alert">
                    {priceError}
                  </div>
                )}
              </div>
            </div>

            <div className="photo-section-box">
              <div className="photo-section-header">
                <label>Фото готового блюда</label>
                <button
                  type="button"
                  className="ai-action-btn"
                  onClick={handleAutoImage}
                  disabled={isImageLoading || !name.trim()}
                  title="Точный поиск фото блюда в Pinterest, Wikipedia и TheMealDB"
                >
                  {isImageLoading ? "Ищем фото..." : "Подобрать фото блюда"}
                </button>
              </div>
              {imageError && (
                <div className="ai-error-message" role="alert">
                  {imageError}
                </div>
              )}
              {imageSource && !imageError && (
                <div className="ai-comment-badge">
                  {imageSource}
                </div>
              )}
              <div className="image-url-row">
                <input
                  type="text"
                  value={image}
                  onChange={e => setImage(e.target.value)}
                  placeholder="URL изображения (или нажмите кнопку автоподбора)"
                  className="image-url-input"
                />
              </div>
              <div className="file-upload-row">
                <input
                  type="file"
                  accept="image/png,image/jpeg"
                  onChange={e =>
                    e.target.files?.[0] &&
                    setImage(URL.createObjectURL(e.target.files[0]))
                  }
                />
              </div>
              <ImageBox src={image} className="form-image" />
              <small>Поддерживаются автоподбор (Pinterest/Wikipedia), прямые ссылки и загрузка файлов</small>
            </div>
          </Card>

          <Card>
            <div className="section-title-with-ai">
              <h3>Пищевая ценность (на 100г)</h3>
              <button
                type="button"
                className="ai-action-btn"
                onClick={handleAutoNutrition}
                disabled={isNutritionLoading || !name.trim()}
                title="Рассчитать калории, белки, жиры и углеводы через ИИ"
              >
                {isNutritionLoading ? "Считаем КБЖУ..." : "Рассчитать КБЖУ через AI"}
              </button>
            </div>

            {nutritionError && (
              <div className="ai-error-message" role="alert">
                {nutritionError}
              </div>
            )}
            {nutritionComment && !nutritionError && (
              <div className="ai-comment-badge" style={{ marginBottom: "12px" }}>
                {nutritionComment}
              </div>
            )}

            <div className="form-grid four">
              <label>
                Калории (ккал)
                <input value={calories} onChange={e => setCalories(e.target.value)} />
              </label>
              <label>
                Белки (г)
                <input value={protein} onChange={e => setProtein(e.target.value)} />
              </label>
              <label>
                Жиры (г)
                <input value={fat} onChange={e => setFat(e.target.value)} />
              </label>
              <label>
                Углеводы (г)
                <input value={carbs} onChange={e => setCarbs(e.target.value)} />
              </label>
            </div>
          </Card>
        </div>

        <div>
          <Card>
            <div className="section-title-with-ai">
              <h3>Шаги приготовления</h3>
              <button
                type="button"
                className="ai-action-btn"
                onClick={handleAutoSteps}
                disabled={isStepsLoading || !name.trim()}
                title="Сгенерировать пошаговый алгоритм приготовления блюда через ИИ"
              >
                {isStepsLoading ? "Генерируем шаги..." : "Сгенерировать шаги через AI"}
              </button>
            </div>

            {stepsError && (
              <div className="ai-error-message" role="alert">
                {stepsError}
              </div>
            )}
            {stepsComment && !stepsError && (
              <div className="ai-comment-badge" style={{ marginBottom: "12px" }}>
                {stepsComment}
              </div>
            )}

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
              <div>
                <div className="section-title-with-ai">
                  <label>Время приготовления (минут)</label>
                  <button
                    type="button"
                    className="ai-action-btn small"
                    onClick={handleAutoTime}
                    disabled={isTimeLoading || !name.trim()}
                    title="Рассчитать время готовки через ИИ"
                  >
                    {isTimeLoading ? "Загрузка..." : "Время через AI"}
                  </button>
                </div>
                {timeError && (
                  <div className="ai-error-message" role="alert">
                    {timeError}
                  </div>
                )}
                {timeComment && !timeError && (
                  <div className="ai-comment-badge" style={{ marginBottom: "6px" }}>
                    {timeComment}
                  </div>
                )}
                <input
                  value={time}
                  onChange={e => setTime(e.target.value)}
                  placeholder="Например: 25"
                />
              </div>

              <label>
                Категория
                <select
                  value={category}
                  onChange={e => setCategory(e.target.value)}
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

      {error && <p role="alert">{error}</p>}
      <div className="right-actions">
        <Button href="/recipes" variant="secondary">
          Отмена
        </Button>
        <Button onClick={save} disabled={saving}>
          {saving ? "Сохраняем..." : mode === "edit" ? "Сохранить изменения" : "Создать рецепт"}
        </Button>
      </div>
    </div>
  );
}
