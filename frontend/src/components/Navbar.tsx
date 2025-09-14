import { Link, NavLink } from 'react-router-dom'
import { useState } from 'react'
import { Bars3Icon, XMarkIcon } from '@heroicons/react/24/outline'

const Navbar = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen)
  }

  return (
    <nav className="bg-bundesliga-dark text-white shadow-md">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center">
              <img 
                src="/logo.svg" 
                alt="Kick Predictor Logo" 
                className="h-8 w-8 mr-2" 
              />
              <span className="font-bold text-xl">Kick Predictor</span>
            </Link>
          </div>
          
          {/* Desktop Menu */}
          <div className="hidden md:flex space-x-8">
            <NavLink 
              to="/" 
              className={({ isActive }) => 
                isActive ? 'font-bold border-b-2 border-bundesliga-red' : 'hover:text-gray-300'
              }
              end
            >
              Home
            </NavLink>
            <NavLink 
              to="/predictions" 
              className={({ isActive }) => 
                isActive ? 'font-bold border-b-2 border-bundesliga-red' : 'hover:text-gray-300'
              }
            >
              Vorhersagen
            </NavLink>
            <NavLink 
              to="/team-analysis" 
              className={({ isActive }) => 
                isActive ? 'font-bold border-b-2 border-bundesliga-red' : 'hover:text-gray-300'
              }
            >
              Team-Analyse
            </NavLink>
            <NavLink 
              to="/table" 
              className={({ isActive }) => 
                isActive ? 'font-bold border-b-2 border-bundesliga-red' : 'hover:text-gray-300'
              }
            >
              Tabelle
            </NavLink>
            <NavLink 
              to="/about" 
              className={({ isActive }) => 
                isActive ? 'font-bold border-b-2 border-bundesliga-red' : 'hover:text-gray-300'
              }
            >
              Über uns
            </NavLink>
          </div>
          
          {/* Mobile Menu Button */}
          <div className="md:hidden">
            <button 
              onClick={toggleMenu}
              className="text-white hover:text-gray-300 focus:outline-none"
            >
              {isMenuOpen ? (
                <XMarkIcon className="h-6 w-6" />
              ) : (
                <Bars3Icon className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>
        
        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="md:hidden pt-2 pb-4 space-y-3">
            <NavLink 
              to="/" 
              className={({ isActive }) => 
                `block py-2 px-4 ${isActive ? 'bg-bundesliga-red font-bold' : 'hover:bg-gray-700'}`
              }
              onClick={toggleMenu}
              end
            >
              Home
            </NavLink>
            <NavLink 
              to="/predictions" 
              className={({ isActive }) => 
                `block py-2 px-4 ${isActive ? 'bg-bundesliga-red font-bold' : 'hover:bg-gray-700'}`
              }
              onClick={toggleMenu}
            >
              Vorhersagen
            </NavLink>
            <NavLink 
              to="/team-analysis" 
              className={({ isActive }) => 
                `block py-2 px-4 ${isActive ? 'bg-bundesliga-red font-bold' : 'hover:bg-gray-700'}`
              }
              onClick={toggleMenu}
            >
              Team-Analyse
            </NavLink>
            <NavLink 
              to="/table" 
              className={({ isActive }) => 
                `block py-2 px-4 ${isActive ? 'bg-bundesliga-red font-bold' : 'hover:bg-gray-700'}`
              }
              onClick={toggleMenu}
            >
              Tabelle
            </NavLink>
            <NavLink 
              to="/about" 
              className={({ isActive }) => 
                `block py-2 px-4 ${isActive ? 'bg-bundesliga-red font-bold' : 'hover:bg-gray-700'}`
              }
              onClick={toggleMenu}
            >
              Über uns
            </NavLink>
          </div>
        )}
      </div>
    </nav>
  )
}

export default Navbar
