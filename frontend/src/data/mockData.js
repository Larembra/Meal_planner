export const user = {
  name: "Константин",
  age: 28,
  height: 182,
  weight: 79,
  role: "Администратор",
  email: "vitya@example.com",
  goal: "Поддерживать форму",
  activity: "Умеренный",
  meals: 4,
  diet: "Всеядный",
  exclusions: ["Арахис", "Коровье молоко"],
  budget: 800,
  cookingTime: 40,
  preferences: "Обожаю рыбу, специи и побольше свежих овощей",
};

export const recipes = [
  {
    id: 1,
    title: "Куриное филе с брокколи в сливках",
    category: "Ужин",
    tag: "Белок",
    time: 25,
    calories: 380,
    price: 430,
    protein: 42,
    fat: 18,
    carbs: 8,
    image: '/static/vitya_nyam_nyam.jpg',
    description: "Нежное куриное филе с брокколи в сливочном соусе.",
    ingredients: [
      { name: "Куриное филе", quantity: "300 г", price: 280, category: "🥩 Мясо и рыба" },
      { name: "Брокколи свежая", quantity: "150 г", price: 90, category: "🥬 Бакалея и овощи" },
      { name: "Сливки 15%", quantity: "100 мл", price: 40, category: "🥛 Молочные продукты" },
      { name: "Оливковое масло", quantity: "10 мл", price: 15, category: "🥬 Бакалея и овощи" },
      { name: "Соль, перец, сухой чеснок", quantity: "по вкусу", price: 5, category: "🧂 Прочее" },
    ],
    steps: [
      "Промойте куриное филе, обсушите бумажным полотенцем и нарежьте средними кусочками. Обжарьте на оливковом масле 5-7 минут.",
      "Разберите брокколи на мелкие соцветия. Добавьте к курице на сковороду, посолите, поперчите и обжаривайте ещё 3 минуты.",
      "Залейте блюдо сливками, добавьте сухой чеснок. Убавьте огонь до минимума и тушите под крышкой в течение 10 минут до загустения сливок.",
    ],
  },
  {
    id: 2,
    title: "Творожная запеканка с курагой",
    category: "Завтрак",
    tag: "Полезно",
    time: 30,
    calories: 310,
    price: 290,
    protein: 28,
    fat: 12,
    carbs: 30,
    image: '/static/vitya_nyam_nyam.jpg',
  },
  {
    id: 3,
    title: "Тыквенный суп-пюре на кокосовом молоке",
    category: "Обед",
    tag: "Веган",
    time: 20,
    calories: 240,
    price: 220,
    protein: 6,
    fat: 10,
    carbs: 30,
    image: '/static/vitya_nyam_nyam.jpg',
  },
  {
    id: 4,
    title: "Салат с тунцом и перепелиными яйцами",
    category: "Перекус",
    tag: "Быстро",
    time: 12,
    calories: 290,
    price: 260,
    protein: 24,
    fat: 14,
    carbs: 12,
    image: '/static/vitya_nyam_nyam.jpg',
  },
  {
    id: 5,
    title: "Запеченная треска под томатным соусом",
    category: "Ужин",
    tag: "Омега-3",
    time: 25,
    calories: 320,
    price: 350,
    protein: 34,
    fat: 12,
    carbs: 14,
    image: '/static/vitya_nyam_nyam.jpg',
  },
  {
    id: 6,
    title: "Гречневая каша с белыми грибами",
    category: "Завтрак",
    tag: "Сложные Уг.",
    time: 18,
    calories: 340,
    price: 240,
    protein: 11,
    fat: 9,
    carbs: 52,
    image: '/static/vitya_nyam_nyam.jpg',
  },
  {
    id: 7,
    title: "Постные щи со свежей капустой",
    category: "Обед",
    tag: "Низкокалорийное",
    time: 40,
    calories: 180,
    price: 180,
    protein: 4,
    fat: 5,
    carbs: 25,
    image: '/static/vitya_nyam_nyam.jpg',
  },
  {
    id: 8,
    title: "Чиа-пудинг на миндальном молоке",
    category: "Перекус",
    tag: "Суперфуд",
    time: 10,
    calories: 210,
    price: 190,
    protein: 7,
    fat: 11,
    carbs: 20,
    image: '/static/vitya_nyam_nyam.jpg',
  },
  {
    id: 9,
    title: "Пышные сырники с рисовой мукой и ягодами",
    category: "Завтрак",
    tag: "Домашнее",
    time: 20,
    calories: 410,
    price: 260,
    protein: 24,
    fat: 12,
    carbs: 51,
    image: '/static/vitya_nyam_nyam.jpg',
    ingredients: [
      { name: "Творог 5% жирности", quantity: "400 г", price: 140, category: "🥛 Молочные продукты" },
      { name: "Куриное яйцо (С1)", quantity: "1 шт.", price: 12, category: "🥛 Молочные продукты" },
      { name: "Рисовая мука", quantity: "3 ст. л.", price: 20, category: "🥬 Бакалея и овощи" },
      { name: "Сахарозаменитель (стевия)", quantity: "по вкусу", price: 15, category: "🥬 Бакалея и овощи" },
      { name: "Ванильный экстракт", quantity: "1/2 ч. л.", price: 18, category: "🥬 Бакалея и овощи" },
      { name: "Свежие ягоды (малина, черника)", quantity: "100 г", price: 55, category: "🥬 Бакалея и овощи" },
    ],
    steps: [
      "Выложите творог в глубокую миску. Разомните его вилкой до однородного состояния, чтобы не было крупных комков.",
      "Добавьте яйцо, рисовую муку, экстракт ванили и заменитель сахара. Тщательно перемешайте массу руками.",
      "Разделите массу на равные части (около 6 штук). Скатайте шарики, слегка прижмите сверху и обваляйте в рисовой муке.",
      "Выложите сырники на разогретую антипригарную сковороду с каплей масла и обжаривайте по 4-5 минут с каждой стороны до золотистой корочки.",
    ],
  },
];

export const dailyMeals = [
  {
    recipeId: 11,
    type: 'Завтрак',
    time: 15,
    title: 'Овсянка на кокосовом молоке с бананом',
    macros: 'Б: 8г | Ж: 12г | У: 54г',
    calories: 350,
    price: 190,
    image: '/static/vitya_nyam_nyam.jpg',
  },
  {
    recipeId: 14,
    type: 'Обед',
    time: 25,
    title: 'Филе трески со шпинатом и рисом',
    macros: 'Б: 36г | Ж: 8г | У: 42г',
    calories: 470,
    price: 260,
    image: '/static/vitya_nyam_nyam.jpg',
  },
  {
    recipeId: 12,
    type: 'Перекус',
    time: 5,
    title: 'Греческий йогурт с горстью миндаля',
    macros: 'Б: 14г | Ж: 14г | У: 12г',
    calories: 220,
    price: 160,
    image: '/static/vitya_nyam_nyam.jpg',
  },
  {
    recipeId: 15,
    type: 'Ужин',
    time: 20,
    title: 'Куриная грудка гриль и брокколи',
    macros: 'Б: 42г | Ж: 6г | У: 8г',
    calories: 380,
    price: 210,
    image: '/static/vitya_nyam_nyam.jpg',
  }
];

export const weeklyMeals = [
  {
    recipeId: 9,
    type: 'Завтрак',
    time: 20,
    title: 'Пышные сырники с рисовой мукой и ягодами',
    description: 'Воздушные сырники из фермерского творога с легкой ноткой ванили, украшенные свежей малиной и черникой.',
    calories: 410,
    price: 260,
    macros: 'Б: 24г | Ж: 12г | У: 51г',
    image: '/static/vitya_nyam_nyam.jpg',
  },
  {
    recipeId: 10,
    type: 'Обед',
    time: 45,
    title: 'Домашний наваристый борщ со сметаной',
    description: 'Классический свекольный борщ на нежирной говяжьей грудинке. Подается с зеленью и ложкой густой сметаны.',
    calories: 520,
    price: 390,
    macros: 'Б: 32г | Ж: 18г | У: 45г',
    image: '/static/vitya_nyam_nyam.jpg',
  },
  {
    recipeId: 12,
    type: 'Перекус',
    time: 5,
    title: 'Греческий йогурт с кедровыми орешками и медом',
    description: 'Натуральный биойогурт без добавок, заправленный жидким липовым медом и подсушенными орешками.',
    calories: 240,
    price: 170,
    macros: 'Б: 12г | Ж: 14г | У: 16г',
    image: '/static/vitya_nyam_nyam.jpg',
  },
  {
    recipeId: 13,
    type: 'Ужин',
    time: 25,
    title: 'Филе форели, запеченное с брокколи и лимоном',
    description: 'Питательный диетический ужин, богатый омега-3 жирными кислотами и качественным протеином.',
    calories: 430,
    price: 290,
    macros: 'Б: 38г | Ж: 16г | У: 10г',
    image: '/static/vitya_nyam_nyam.jpg',
  }
];

export const mealRecipes = [
  {
    id: 10,
    title: 'Домашний наваристый борщ со сметаной',
    category: 'Обед',
    tag: 'Домашнее',
    time: 45,
    calories: 520,
    price: 390,
    protein: 32,
    fat: 18,
    carbs: 45,
    image: '/static/vitya_nyam_nyam.jpg',
    ingredients: [
      { name: 'Говяжья грудинка', quantity: '400 г', price: 220, category: '🥩 Мясо и рыба' },
      { name: 'Свекла', quantity: '2 шт.', price: 40, category: '🥬 Бакалея и овощи' },
      { name: 'Капуста', quantity: '250 г', price: 35, category: '🥬 Бакалея и овощи' },
      { name: 'Морковь', quantity: '1 шт.', price: 15, category: '🥬 Бакалея и овощи' },
      { name: 'Сметана 15%', quantity: '60 г', price: 80, category: '🥛 Молочные продукты' },
    ],
    steps: [
      'Отварите говядину до готовности и подготовьте овощи.',
      'Добавьте свеклу, морковь и капусту в бульон.',
      'Подавайте готовый борщ со сметаной и свежей зеленью.'
    ]
  },
  {
    id: 11,
    title: 'Овсянка на кокосовом молоке с бананом',
    category: 'Завтрак',
    tag: 'Быстро',
    time: 15,
    calories: 350,
    price: 190,
    protein: 8,
    fat: 12,
    carbs: 54,
    image: '/static/vitya_nyam_nyam.jpg',
    ingredients: [
      { name: 'Овсяные хлопья', quantity: '60 г', price: 25, category: '🥬 Бакалея и овощи' },
      { name: 'Кокосовое молоко', quantity: '200 мл', price: 110, category: '🥛 Молочные продукты' },
      { name: 'Банан', quantity: '1 шт.', price: 40, category: '🥬 Бакалея и овощи' },
      { name: 'Корица', quantity: 'по вкусу', price: 15, category: '🧂 Прочее' },
    ],
    steps: [
      'Нагрейте кокосовое молоко и добавьте овсяные хлопья.',
      'Варите кашу до мягкости, периодически помешивая.',
      'Добавьте банан и корицу перед подачей.'
    ]
  },
  {
    id: 12,
    title: 'Греческий йогурт с горстью миндаля',
    category: 'Перекус',
    tag: 'Быстро',
    time: 5,
    calories: 220,
    price: 160,
    protein: 14,
    fat: 14,
    carbs: 12,
    image: '/static/vitya_nyam_nyam.jpg',
    ingredients: [
      { name: 'Греческий йогурт 2%', quantity: '200 г', price: 90, category: '🥛 Молочные продукты' },
      { name: 'Миндаль', quantity: '25 г', price: 55, category: '🥬 Бакалея и овощи' },
      { name: 'Мед', quantity: '1 ч. л.', price: 15, category: '🥬 Бакалея и овощи' },
    ],
    steps: [
      'Переложите йогурт в миску.',
      'Добавьте миндаль и немного меда.',
      'Перемешайте и подавайте охлажденным.'
    ]
  },
  {
    id: 13,
    title: 'Филе форели, запеченное с брокколи и лимоном',
    category: 'Ужин',
    tag: 'Омега-3',
    time: 25,
    calories: 430,
    price: 290,
    protein: 38,
    fat: 16,
    carbs: 10,
    image: '/static/vitya_nyam_nyam.jpg',
    ingredients: [
      { name: 'Филе форели', quantity: '180 г', price: 210, category: '🥩 Мясо и рыба' },
      { name: 'Брокколи', quantity: '150 г', price: 50, category: '🥬 Бакалея и овощи' },
      { name: 'Лимон', quantity: '1/2 шт.', price: 15, category: '🥬 Бакалея и овощи' },
      { name: 'Оливковое масло', quantity: '1 ч. л.', price: 10, category: '🥬 Бакалея и овощи' },
      { name: 'Соль и перец', quantity: 'по вкусу', price: 5, category: '🧂 Прочее' },
    ],
    steps: [
      'Подготовьте форель и брокколи.',
      'Приправьте рыбу, добавьте лимон и немного масла.',
      'Запекайте вместе с брокколи до готовности.'
    ]
  },
  {
    id: 14,
    title: 'Филе трески со шпинатом и рисом',
    category: 'Обед',
    tag: 'Белок',
    time: 25,
    calories: 470,
    price: 260,
    protein: 36,
    fat: 8,
    carbs: 42,
    image: '/static/vitya_nyam_nyam.jpg',
    ingredients: [
      { name: 'Филе трески', quantity: '180 г', price: 185, category: '🥩 Мясо и рыба' },
      { name: 'Шпинат', quantity: '80 г', price: 40, category: '🥬 Бакалея и овощи' },
      { name: 'Рис', quantity: '70 г', price: 20, category: '🥬 Бакалея и овощи' },
      { name: 'Оливковое масло', quantity: '1 ч. л.', price: 10, category: '🥬 Бакалея и овощи' },
      { name: 'Соль и перец', quantity: 'по вкусу', price: 5, category: '🧂 Прочее' },
    ],
    steps: [
      'Отварите рис до готовности.',
      'Приправьте филе трески и обжарьте до готовности.',
      'Добавьте шпинат и подавайте рыбу с рисом.'
    ]
  },
  {
    id: 15,
    title: 'Куриная грудка гриль и брокколи',
    category: 'Ужин',
    tag: 'Белок',
    time: 20,
    calories: 380,
    price: 210,
    protein: 42,
    fat: 6,
    carbs: 8,
    image: '/static/vitya_nyam_nyam.jpg',
    ingredients: [
      { name: 'Куриная грудка', quantity: '200 г', price: 140, category: '🥩 Мясо и рыба' },
      { name: 'Брокколи', quantity: '150 г', price: 50, category: '🥬 Бакалея и овощи' },
      { name: 'Оливковое масло', quantity: '1 ч. л.', price: 15, category: '🥬 Бакалея и овощи' },
      { name: 'Соль, перец и специи', quantity: 'по вкусу', price: 5, category: '🧂 Прочее' },
    ],
    steps: [
      'Приправьте куриную грудку и обжарьте на гриле до готовности.',
      'Приготовьте брокколи на пару или быстро обжарьте.',
      'Подавайте куриную грудку с брокколи.'
    ]
  }
];

export const ingredientCategories = [
  '🥛 Молочные продукты',
  '🥩 Мясо и рыба',
  '🥬 Бакалея и овощи',
  '🧂 Прочее',
]

export function dietRecipes() {
  const ids = [...new Set([
    ...weeklyMeals.map(meal => meal.recipeId),
    ...dailyMeals.map(meal => meal.recipeId),
  ])]
  const all = [...recipes, ...mealRecipes]
  return ids.map(id => all.find(recipe => recipe.id === id)).filter(Boolean)
}

export function buildShoppingGroups(sourceRecipes = dietRecipes()) {
  const groups = ingredientCategories.map(title => ({ title, items: [] }))
  const indexByTitle = Object.fromEntries(ingredientCategories.map((title, i) => [title, i]))
  const merged = new Map()

  sourceRecipes.forEach(recipe => {
    (recipe.ingredients || []).forEach((ing, i) => {
      const title = indexByTitle[ing.category] != null
        ? ing.category
        : '🧂 Прочее'
      const key = `${title}::${ing.name}`
      if (merged.has(key)) {
        const prev = merged.get(key)
        prev.price += Number(ing.price) || 0
        return
      }
      merged.set(key, {
        id: `${title}-${ing.name}-${recipe.id}-${i}`,
        name: ing.name,
        quantity: ing.quantity,
        price: Number(ing.price) || 0,
        category: title,
      })
    })
  })

  merged.forEach(item => {
    groups[indexByTitle[item.category]].items.push(item)
  })

  return groups.filter(group => group.items.length)
}

export const shoppingGroups = buildShoppingGroups()

export function sumIngredientPrices(ingredients = []) {
  return ingredients.reduce((sum, item) => {
    if (!item || typeof item !== 'object') return sum
    return sum + (Number(item.price) || 0)
  }, 0)
}

export function ingredientText(item) {
  if (!item) return ''
  if (typeof item === 'string') return item
  return [item.name, item.quantity].filter(Boolean).join(' ')
}


