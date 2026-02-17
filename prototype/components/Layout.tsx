
import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-[#0a1428] border-b border-[#1e2328] sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-2 group">
            <div className="w-8 h-8 bg-[#c8aa6e] rounded-sm transform rotate-45 flex items-center justify-center transition-transform group-hover:scale-110">
              <div className="w-4 h-4 bg-[#0a1428] transform rotate-45"></div>
            </div>
            <span className="lol-font text-2xl tracking-widest text-[#c8aa6e] uppercase">NexusStats</span>
          </Link>
          <nav className="hidden md:flex space-x-8">
            <Link 
              to="/" 
              className={`font-medium transition-colors ${isActive('/') ? 'text-[#c8aa6e]' : 'text-gray-400 hover:text-white'}`}
            >
              Home
            </Link>
            <Link 
              to="/champions" 
              className={`font-medium transition-colors ${isActive('/champions') ? 'text-[#c8aa6e]' : 'text-gray-400 hover:text-white'}`}
            >
              Champions
            </Link>
            <Link 
              to="/items" 
              className={`font-medium transition-colors ${isActive('/items') ? 'text-[#c8aa6e]' : 'text-gray-400 hover:text-white'}`}
            >
              Items
            </Link>
            <Link 
              to="/pro-play" 
              className={`font-medium transition-colors ${isActive('/pro-play') ? 'text-[#c8aa6e]' : 'text-gray-400 hover:text-white'}`}
            >
              Pro Play
            </Link>
            <Link 
              to="/leaderboards" 
              className={`font-medium transition-colors ${isActive('/leaderboards') ? 'text-[#c8aa6e]' : 'text-gray-400 hover:text-white'}`}
            >
              Leaderboards
            </Link>
          </nav>
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => navigate('/login')}
              className="bg-transparent border border-[#c8aa6e] text-[#c8aa6e] px-4 py-1.5 rounded-sm hover:bg-[#c8aa6e] hover:text-[#0a1428] transition-all text-sm font-semibold uppercase tracking-wider"
            >
              Login
            </button>
          </div>
        </div>
      </header>

      <main className="flex-grow">
        {children}
      </main>

      <footer className="bg-[#0a1428] border-t border-[#1e2328] py-8 mt-12">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="text-gray-500 text-sm">
            NexusStats isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing League of Legends.
          </p>
          <div className="mt-4 flex justify-center space-x-6">
            <a href="#" className="text-gray-400 hover:text-white text-sm transition-colors">Privacy Policy</a>
            <a href="#" className="text-gray-400 hover:text-white text-sm transition-colors">Terms of Service</a>
            <a href="#" className="text-gray-400 hover:text-white text-sm transition-colors">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
