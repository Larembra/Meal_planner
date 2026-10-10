import React, { useEffect, useMemo, useState } from 'react'
import { Button, Card, ImageBox } from '../components/UI'
import { recipes, sumIngredientPrices } from '../data/mockData'
import { deleteRecipe, getRecipes } from '../api'

export default function Recipes() {
  const [apiRecipes, setApiRecipes] = useState([])
  const [apiError, setApiError] = useState('')
  const [apiLoaded, setApiLoaded] = useState(false)
  useEffect(() => {
    getRecipes()
      .then(value => {
        setApiRecipes(value)
        setApiLoaded(true)
      })
      .catch(err => setApiError(err.message))
  }, [])
  const [q, setQ] = useState('')
  const [cat, setCat] = useState('Все блюда')
  const [quickFilters, setQuickFilters] = useState([])
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [tagQuery, setTagQuery] = useState('')
  const [draftTags, setDraftTags] = useState([])
  const [selectedTags, setSelectedTags] = useState([])
  const sourceRecipes = apiLoaded ? apiRecipes : recipes
  const recipeTags = useMemo(
    () => [...new Set([
      ...sourceRecipes.flatMap(r => r.tags || [r.tag]).filter(Boolean),
      'Избранное',
    ])],
    [sourceRecipes]
  )

  const toggleQuickFilter = filter => {
    setQuickFilters(filters =>
      filters.includes(filter)
        ? filters.filter(item => item !== filter)
        : [...filters, filter]
    )
  }

  const toggleDraftTag = tag => {
    setDraftTags(tags =>
      tags.includes(tag) ? tags.filter(item => item !== tag) : [...tags, tag]
    )
  }

  const openFilters = () => {
    setDraftTags(selectedTags)
    setTagQuery('')
    setFiltersOpen(open => !open)
  }

  const applyTagFilters = () => {
    setSelectedTags(draftTags)
    setFiltersOpen(false)
    setTagQuery('')
  }

  const matchingTags = useMemo(() => {
    const query = tagQuery.trim().toLowerCase()
    if (!query) return []
    return recipeTags.filter(tag => tag.toLowerCase().includes(query))
  }, [tagQuery, recipeTags])

  const unselectedMatches = matchingTags.filter(tag => !draftTags.includes(tag))
  const favoriteTag = 'Избранное'

  const isModerator = JSON.parse(localStorage.getItem("meal_planner_user") || "null")?.role === "admin"
  const [favorites, setFavorites] = useState(() => JSON.parse(localStorage.getItem("favorite_recipes") || "[]"))
  const toggleFavorite = id => setFavorites(previous => {
    const next = previous.includes(id) ? previous.filter(item => item !== id) : [...previous, id]
    localStorage.setItem("favorite_recipes", JSON.stringify(next))
    return next
  })
  const removeRecipe = async (event, recipe) => {
    event.stopPropagation()
    if (!window.confirm(`Удалить рецепт «${recipe.title}» полностью?`)) return
    try {
      await deleteRecipe(recipe.id)
      setApiRecipes(previous => previous.filter(item => item.id !== recipe.id))
    } catch (err) {
      setApiError(err.message)
    }
  }
  const list = useMemo(
    () => sourceRecipes.filter(r => {
      const matchesQuery = [
        r.title,
        r.description,
        ...(r.ingredients || []).map(item =>
          typeof item === 'string' ? item : [item.name, item.quantity].filter(Boolean).join(' ')
        )
      ]
        .join(' ')
        .toLowerCase()
        .includes(q.toLowerCase())

      const matchesCategory = cat === 'Все блюда' || r.category === cat

      const recipeTagValues = r.tags || [r.tag]
      const matchesTags = selectedTags.length === 0 || selectedTags.some(tag =>
        tag === favoriteTag ? favorites.includes(r.id) : recipeTagValues.includes(tag)
      )

      const matchesQuickFilters = quickFilters.every(filter => {
        if (filter === favoriteTag) return favorites.includes(r.id)
        if (filter === 'Меньше 20 минут') return r.time < 20
        if (filter === 'Высокобелковые') return r.protein >= 30
        if (filter === 'До 300 рублей') {
          const price = sumIngredientPrices(r.ingredients) || Number(r.price || 0)
          return price <= 300
        }
        return true
      })

      return matchesQuery && matchesCategory && matchesTags && matchesQuickFilters
    }),
    [q, cat, selectedTags, quickFilters, sourceRecipes, favorites]
  )

  const cats = [
    ['Все блюда', 'Все блюда'],
    ['Завтраки', 'Завтрак'],
    ['Обеды', 'Обед'],
    ['Ужины', 'Ужин'],
    ['Перекусы', 'Перекус']
  ]

  const quick = ['Избранное', 'Меньше 20 минут', 'Высокобелковые', 'До 300 рублей']

  const openRecipe = id => {
    window.location.href = `/recipes/${id}`
  }

  const handleCardKeyDown = (event, id) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      openRecipe(id)
    }
  }

  return (
    <div className="container">
      <div className="page-title">
        <div>
          <h1>Книга рецептов</h1>
          <p>База здоровых и простых блюд</p>
        </div>

        {isModerator && <Button href="/recipes/new">+ Создать рецепт</Button>}
      </div>

      <div className="search-row">
        <input
          value={q}
          onChange={e => setQ(e.target.value)}
          placeholder="⌕  Поиск рецептов (например: овсянка, лосось, курица)..."
        />

        <div className="filters-wrap">
          <Button
            variant="secondary"
            className={selectedTags.length ? 'filters-active' : ''}
            aria-expanded={filtersOpen}
            onClick={openFilters}
          >
            Фильтры 🧪
          </Button>

          {filtersOpen && (
            <>
              <div
                className="filters-backdrop"
                onClick={() => setFiltersOpen(false)}
              />
              <div className="filters-panel" role="dialog" aria-label="Фильтры по тегам">
                <input
                  autoFocus
                  value={tagQuery}
                  onChange={e => setTagQuery(e.target.value)}
                  placeholder="Найти тег: белок, веган, быстро..."
                />

                {draftTags.length > 0 && (
                  <div className="chips">
                    {draftTags.map(tag => (
                      <button
                        key={tag}
                        type="button"
                        className="selected"
                        onClick={() => toggleDraftTag(tag)}
                      >
                        {tag}
                      </button>
                    ))}
                  </div>
                )}

                {tagQuery.trim() ? (
                  unselectedMatches.length > 0 ? (
                    <div className="chips">
                      {unselectedMatches.map(tag => (
                        <button
                          key={tag}
                          type="button"
                          onClick={() => toggleDraftTag(tag)}
                        >
                          {tag}
                        </button>
                      ))}
                    </div>
                  ) : matchingTags.length === 0 ? (
                    <p className="filters-hint">Теги не найдены</p>
                  ) : null
                ) : (
                  <p className="filters-hint">Начните вводить название тега</p>
                )}

                <Button onClick={applyTagFilters}>Применить</Button>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="chips">
        {cats.map(([label, value]) => (
          <button
            key={label}
            onClick={() => setCat(value)}
            className={cat === value ? 'selected' : ''}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="chips quick-filters">
        {quick.map(filter => (
          <button
            key={filter}
            onClick={() => toggleQuickFilter(filter)}
            className={quickFilters.includes(filter) ? 'selected' : ''}
          >
            {filter}
          </button>
        ))}
      </div>

      <div className="recipe-grid">
        {apiError && <p role="alert">{apiError}</p>}
        {list.map(r => (
          <Card
            key={r.id}
            className="recipe-card recipe-card-clickable"
            onClick={() => openRecipe(r.id)}
            onKeyDown={event => handleCardKeyDown(event, r.id)}
            role="link"
            tabIndex={0}
          >
            <ImageBox src={r.image} />

            <div className="recipe-body">
              <div className="tags">
                <span>{r.category}</span>
                <span>{r.tag}</span>
                {favorites.includes(r.id) && <span>Избранное</span>}
              </div>

              <h3>{r.title}</h3>

              <div className="recipe-meta">
                <span>◷ {r.time} мин</span>
                <strong>{r.calories} ккал | Б: {r.protein}г</strong>
              </div>

              <div className="recipe-price">Цена: {sumIngredientPrices(r.ingredients) || r.price || 0} ₽</div>

              <button type="button" className="edit-icon favorite-icon"
                title={favorites.includes(r.id) ? "Убрать из избранного" : "Добавить в избранное"}
                aria-label={favorites.includes(r.id) ? "Убрать из избранного" : "Добавить в избранное"}
                onClick={event => { event.stopPropagation(); toggleFavorite(r.id) }}
                onKeyDown={event => event.stopPropagation()}
              >{favorites.includes(r.id) ? "♥" : "♡"}</button>
              {isModerator && <a
                className="edit-icon edit-recipe-icon"
                href={`/recipes/edit?id=${r.id}`}
                title="Редактировать"
                aria-label={`Редактировать рецепт ${r.title}`}
                onClick={event => event.stopPropagation()}
                onKeyDown={event => event.stopPropagation()}
              >
                ✎
              </a>}
              {isModerator && <button
                type="button"
                className="edit-icon delete-recipe-icon"
                title="Удалить рецепт полностью"
                aria-label={`Удалить рецепт ${r.title}`}
                onClick={event => removeRecipe(event, r)}
                onKeyDown={event => event.stopPropagation()}
              >
                ×
              </button>}
            </div>
          </Card>
        ))}
      </div>

      <Card className="dark-cta">
        <div>
          <h2>Затрудняетесь с выбором?</h2>
          <p>
            Витя подготовит уникальный рацион с учетом Ваших предпочтений.
          </p>
        </div>

        <Button href="/diet/generate">Создать рацион</Button>
      </Card>
    </div>
  )
}
