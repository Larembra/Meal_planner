import React, { useMemo, useState } from 'react'
import { Button, Card, ImageBox } from '../components/UI'
import { recipes, sumIngredientPrices } from '../data/mockData'

const recipeTags = [...new Set(recipes.map(r => r.tag).filter(Boolean))]

export default function Recipes() {
  const [q, setQ] = useState('')
  const [cat, setCat] = useState('Все блюда')
  const [quickFilters, setQuickFilters] = useState([])
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [tagQuery, setTagQuery] = useState('')
  const [draftTags, setDraftTags] = useState([])
  const [selectedTags, setSelectedTags] = useState([])

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
  }, [tagQuery])

  const unselectedMatches = matchingTags.filter(tag => !draftTags.includes(tag))

  const list = useMemo(
    () => recipes.filter(r => {
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

      const matchesTags =
        selectedTags.length === 0 || selectedTags.includes(r.tag)

      const matchesQuickFilters = quickFilters.every(filter => {
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
    [q, cat, selectedTags, quickFilters]
  )

  const cats = [
    ['Все блюда', 'Все блюда'],
    ['Завтраки', 'Завтрак'],
    ['Обеды', 'Обед'],
    ['Ужины', 'Ужин'],
    ['Перекусы', 'Перекус']
  ]

  const quick = ['Меньше 20 минут', 'Высокобелковые', 'До 300 рублей']

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

        <Button href="/recipes/new">+ Создать рецепт</Button>
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
              </div>

              <h3>{r.title}</h3>

              <div className="recipe-meta">
                <span>◷ {r.time} мин</span>
                <strong>{r.calories} ккал | Б: {r.protein}г</strong>
              </div>

              <div className="recipe-price">Цена: {sumIngredientPrices(r.ingredients) || r.price || 0} ₽</div>

              <a
                className="edit-icon"
                href={`/recipes/edit?id=${r.id}`}
                title="Редактировать"
                aria-label={`Редактировать рецепт ${r.title}`}
                onClick={event => event.stopPropagation()}
                onKeyDown={event => event.stopPropagation()}
              >
                ✎
              </a>
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