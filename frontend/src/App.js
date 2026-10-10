import React from 'react'
import Layout from './components/Layout'
import { Home } from './pages/Home'
import Register from './pages/Register'
import Login from './pages/Login'
import Profile from './pages/Profile'
import GenerateDiet from './pages/GenerateDiet'
import WeeklyDiet from './pages/WeeklyDiet'
import Recipes from './pages/Recipes'
import RecipeDetail from './pages/RecipeDetail'
import Shopping from './pages/Shopping'
import Tracking from './pages/Tracking'
import RecipeForm from './pages/RecipeForm'

function Router() {
  const path = window.location.pathname
  if (path === '/register') return <Register />
  if (path === '/login') return <Login />
  const authenticated = Boolean(localStorage.getItem('meal_planner_access_token'))
  if (!authenticated && path !== '/') {
    window.location.replace('/login')
    return null
  }
  const currentUser = JSON.parse(localStorage.getItem('meal_planner_user') || 'null')
  if ((path === '/recipes/new' || path === '/recipes/edit') && currentUser?.role !== 'admin') {
    window.location.replace('/recipes')
    return null
  }
  let page
  if (path === '/') page = <Home />
  else if (path === '/profile') page = <Profile />
  else if (path === '/diet/today' || path === '/diet/week') page = <WeeklyDiet />
  else if (path === '/diet/generate') page = <GenerateDiet />
  else if (path === '/recipes') page = <Recipes />
  else if (path === '/recipes/new') page = <RecipeForm mode="create" />
  else if (path === '/recipes/edit') page = <RecipeForm mode="edit" />
  else if (path.startsWith('/recipes/')) page = <RecipeDetail />
  else if (path === '/shopping') page = <Shopping />
  else if (path === '/tracking') page = <Tracking />
  else page = <Home />
  return <Layout>{page}</Layout>
}

export default function App() { return <Router /> }
