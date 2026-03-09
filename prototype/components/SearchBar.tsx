
import React, { useState } from 'react';
import { REGIONS, Icons } from '../constants';

interface SearchBarProps {
  onSearch: (name: string, region: string) => void;
  isLoading?: boolean;
}

const SearchBar: React.FC<SearchBarProps> = ({ onSearch, isLoading }) => {
  const [name, setName] = useState('');
  const [region, setRegion] = useState('na');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim()) {
      onSearch(name.trim(), region);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="relative group">
        <div className="flex flex-col md:flex-row gap-2 bg-[#0a1428]/80 p-2 border border-[#1e2328] rounded shadow-2xl backdrop-blur-md group-focus-within:border-[#c89b3c] transition-all">
          <div className="relative flex-grow">
             <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Search for a Summoner..."
              className="w-full bg-transparent text-white px-4 py-3 outline-none placeholder-gray-500 text-lg"
            />
          </div>
          
          <div className="flex gap-2">
            <select
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              className="bg-[#1e2328] text-white px-4 py-2 border border-[#3c3c41] rounded focus:border-[#c89b3c] outline-none cursor-pointer hover:bg-[#2a2f35] transition-colors appearance-none pr-10 relative"
              style={{ backgroundImage: `url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>')`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 10px center' }}
            >
              {REGIONS.map((reg) => (
                <option key={reg.value} value={reg.value} className="bg-[#1e2328]">
                  {reg.label}
                </option>
              ))}
            </select>

            <button
              type="submit"
              disabled={isLoading}
              className={`flex items-center justify-center px-8 py-3 rounded font-bold uppercase tracking-wider transition-all shadow-lg ${
                isLoading 
                  ? 'bg-gray-700 text-gray-400 cursor-not-allowed' 
                  : 'bg-[#c8aa6e] hover:bg-[#c89b3c] text-[#0a1428]'
              }`}
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <div className="flex items-center gap-2">
                  <Icons.Search />
                  <span>Search</span>
                </div>
              )}
            </button>
          </div>
        </div>
        
        {/* Subtle glow effect */}
        <div className="absolute -inset-0.5 bg-[#c8aa6e]/10 blur opacity-0 group-focus-within:opacity-100 transition duration-500 rounded pointer-events-none"></div>
      </form>
    </div>
  );
};

export default SearchBar;
