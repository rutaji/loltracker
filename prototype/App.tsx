
import React, { useState, useEffect, useMemo } from 'react';
import { HashRouter as Router, Routes, Route, useNavigate, Link } from 'react-router-dom';
import Layout from './components/Layout';
import SearchBar from './components/SearchBar';
import PlayerStats from './components/PlayerStats';
import MatchHistory from './components/MatchHistory';
import { geminiService } from './services/geminiService';
import { PlayerSummary, Match, Item } from './types';

const LoginPage = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    alert("Logged in successfully!");
    navigate('/');
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="bg-[#0a1428] border border-[#c8aa6e]/30 p-8 rounded shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[#c8aa6e] to-transparent"></div>
          
          <div className="flex flex-col items-center mb-8">
            <div className="w-12 h-12 bg-[#c8aa6e] rounded-sm transform rotate-45 flex items-center justify-center mb-4">
              <div className="w-6 h-6 bg-[#0a1428] transform rotate-45"></div>
            </div>
            <h1 className="lol-font text-3xl text-[#c8aa6e] uppercase tracking-widest">Sign In</h1>
            <p className="text-gray-500 text-xs uppercase mt-2 font-bold tracking-widest">Access your Nexus account</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            <div className="space-y-2">
              <label className="text-gray-400 text-[10px] font-bold uppercase tracking-widest px-1">Email Address</label>
              <input 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-[#1e2328] border border-[#3c3c41] rounded px-4 py-3 text-white focus:border-[#c8aa6e] outline-none transition-colors"
                placeholder="summoner@rift.com"
              />
            </div>

            <div className="space-y-2">
              <label className="text-gray-400 text-[10px] font-bold uppercase tracking-widest px-1">Password</label>
              <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full bg-[#1e2328] border border-[#3c3c41] rounded px-4 py-3 text-white focus:border-[#c8aa6e] outline-none transition-colors"
                placeholder="••••••••"
              />
            </div>

            <button 
              type="submit"
              className="w-full bg-[#c8aa6e] hover:bg-[#c89b3c] text-[#0a1428] font-black uppercase py-4 rounded transition-all shadow-lg active:scale-[0.98]"
            >
              Enter the Rift
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

const HomePage = () => {
  const navigate = useNavigate();

  const handleSearch = (name: string, region: string) => {
    navigate(`/profile/${region}/${name}`);
  };

  const featuredSummoners = [
    { name: 'Faker', region: 'kr', tag: 'T1' },
    { name: 'Caps', region: 'euw', tag: 'G2' },
    { name: 'Doublelift', region: 'na', tag: 'LIFT' },
    { name: 'Chovy', region: 'kr', tag: 'GEN' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-12 md:py-24">
      <div className="text-center mb-16 relative">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-blue-600/10 blur-[120px] pointer-events-none rounded-full"></div>
        <h1 className="lol-font text-5xl md:text-7xl mb-4 text-[#c8aa6e] uppercase tracking-tighter drop-shadow-2xl">
          Evolve your Game
        </h1>
        <p className="text-gray-400 text-lg md:text-xl max-w-2xl mx-auto font-light">
          Analyze summoner performance, track your progress, and stay updated with the global League of Legends scene.
        </p>
      </div>

      <SearchBar onSearch={handleSearch} />

      <div className="mt-8 flex flex-col items-center">
        <div className="text-xs text-gray-500 uppercase font-bold mb-3 tracking-widest">Trending Summoners</div>
        <div className="flex flex-wrap justify-center gap-3">
          {featuredSummoners.map((s) => (
            <button
              key={s.name}
              onClick={() => handleSearch(s.name, s.region)}
              className="bg-[#1e2328] border border-[#3c3c41] hover:border-[#c8aa6e] text-gray-300 hover:text-white px-4 py-1.5 rounded-full text-xs transition-all flex items-center gap-2"
            >
              <span className="font-bold">{s.name}</span>
              <span className="text-gray-500 text-[10px]">{s.region.toUpperCase()}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="mt-24">
      </div>
    </div>
  );
};

const ChampionDetailsModal = ({ championName, onClose }: { championName: string, onClose: () => void }) => {
  const [details, setDetails] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedVersion, setSelectedVersion] = useState<string>('');

  useEffect(() => {
    geminiService.getChampionDetails(championName).then(data => {
      setDetails(data);
      if (data.globalStats && data.globalStats.length > 0) {
        setSelectedVersion(data.globalStats[0].version);
      }
      setLoading(false);
    });
  }, [championName]);

  const currentStats = useMemo(() => {
    if (!details || !details.globalStats) return null;
    return details.globalStats.find((s: any) => s.version === selectedVersion) || details.globalStats[0];
  }, [details, selectedVersion]);

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-[#010a13]/90 backdrop-blur-sm animate-fadeIn">
      <div className="bg-[#0a1428] border border-[#c8aa6e]/30 w-full max-w-3xl max-h-[90vh] overflow-hidden rounded relative flex flex-col">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[#c8aa6e] to-transparent"></div>
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-500 hover:text-white transition-colors p-2"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
        </button>

        <div className="p-8 overflow-y-auto">
          {loading ? (
            <div className="flex flex-col items-center py-20 gap-4">
              <div className="w-10 h-10 border-4 border-[#c8aa6e] border-t-transparent rounded-full animate-spin"></div>
              <span className="text-[#c8aa6e] uppercase tracking-widest font-bold text-sm italic">Accessing Archives...</span>
            </div>
          ) : (
            <>
              <h2 className="lol-font text-4xl text-[#c8aa6e] uppercase tracking-tighter mb-4 border-b border-[#1e2328] pb-4">{details.name}</h2>
              
              <div className="mb-8 bg-[#1e2328]/50 rounded p-4 border border-[#3c3c41] flex flex-wrap gap-6 justify-between">
                <div className="flex flex-col">
                  <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-1">Health</span>
                  <span className="text-[#c8aa6e] font-black italic">{details.stats.health}</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-1">Mana</span>
                  <span className="text-[#c8aa6e] font-black italic">{details.stats.mana}</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-1">Attack Damage</span>
                  <span className="text-[#c8aa6e] font-black italic">{details.stats.attackDamage}</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-1">Armor</span>
                  <span className="text-[#c8aa6e] font-black italic">{details.stats.armor}</span>
                </div>
              </div>

              <h3 className="text-white text-xs font-bold uppercase tracking-widest mb-4 italic opacity-70">Combat Abilities</h3>
              <div className="space-y-8">
                {details.abilities.map((ability: any) => (
                  <div key={ability.key} className="flex gap-6 group">
                    <div className="w-16 h-16 bg-[#1e2328] border border-[#3c3c41] group-hover:border-[#c8aa6e] transition-colors rounded shrink-0 flex items-center justify-center text-2xl font-black text-[#c8aa6e] italic">
                      {ability.key}
                    </div>
                    <div>
                      <h4 className="text-white font-bold text-lg uppercase tracking-wide mb-1">{ability.name}</h4>
                      <p className="text-gray-400 text-sm leading-relaxed">{ability.description}</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-12 pt-8 border-t border-[#1e2328]">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                  <h3 className="text-white text-xs font-bold uppercase tracking-widest italic opacity-70">Global Performance Statistics</h3>
                  <div className="flex items-center gap-3">
                    <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Version</span>
                    <select 
                      value={selectedVersion} 
                      onChange={(e) => setSelectedVersion(e.target.value)}
                      className="bg-[#0a1428] border border-[#3c3c41] text-[#c8aa6e] text-[10px] font-bold uppercase px-3 py-1.5 rounded outline-none focus:border-[#c8aa6e] transition-colors"
                    >
                      {details.globalStats.map((s: any) => (
                        <option key={s.version} value={s.version}>Patch {s.version}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {currentStats && (
                  <div className="bg-[#1e2328]/30 border border-[#3c3c41] rounded p-6 animate-fadeIn">
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
                      {currentStats.winRates.map((modeStat: any, mIdx: number) => (
                        <div key={mIdx} className="flex flex-col gap-3">
                          <div className="flex justify-between items-end">
                            <span className="text-gray-400 text-[10px] font-bold uppercase tracking-widest">{modeStat.mode}</span>
                            <span className={`text-sm font-black italic ${modeStat.winRate >= 50 ? 'text-emerald-400' : 'text-red-400'}`}>
                              {modeStat.winRate}%
                            </span>
                          </div>
                          <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
                            <div 
                              className={`h-full transition-all duration-500 ease-out ${modeStat.winRate >= 50 ? 'bg-emerald-500' : 'bg-red-500'}`} 
                              style={{ width: `${modeStat.winRate}%` }}
                            ></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
        <div className="bg-[#1e2328] p-4 text-center border-t border-[#0a1428]">
          <button onClick={onClose} className="text-[#c8aa6e] font-bold uppercase tracking-widest text-xs hover:text-white transition-colors">Close Dossier</button>
        </div>
      </div>
    </div>
  );
};

const ChampionsPage = () => {
  const [champions, setChampions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedChamp, setSelectedChamp] = useState<string | null>(null);
  const [filterRole, setFilterRole] = useState('All');
  const [sortBy, setSortBy] = useState('name-asc');

  useEffect(() => {
    geminiService.getChampions().then(data => {
      setChampions(data);
      setLoading(false);
    });
  }, []);

  const roles = useMemo(() => {
    const r = new Set<string>(['All']);
    champions.forEach(c => r.add(c.role));
    return Array.from(r);
  }, [champions]);

  const filteredAndSortedChampions = useMemo(() => {
    let result = [...champions];
    if (filterRole !== 'All') result = result.filter(c => c.role === filterRole);
    result.sort((a, b) => {
      switch (sortBy) {
        case 'name-asc': return a.name.localeCompare(b.name);
        case 'name-desc': return b.name.localeCompare(a.name);
        case 'difficulty-asc': return a.difficulty.localeCompare(b.difficulty);
        case 'difficulty-desc': return b.difficulty.localeCompare(a.difficulty);
        default: return 0;
      }
    });
    return result;
  }, [champions, filterRole, sortBy]);

  if (loading) return <div className="p-20 text-center text-[#c8aa6e] animate-pulse uppercase tracking-widest font-bold">Summoning Champions...</div>;

  return (
    <div className="max-w-7xl mx-auto px-4 py-12">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
        <div>
          <h1 className="lol-font text-5xl text-[#c8aa6e] uppercase tracking-tighter mb-2">Champions</h1>
          <p className="text-gray-500 text-sm font-bold uppercase tracking-widest italic">Database of Legend</p>
        </div>
        <div className="flex flex-wrap gap-4">
          <div className="flex flex-col gap-1.5">
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest px-1">Filter by Role</span>
            <select value={filterRole} onChange={(e) => setFilterRole(e.target.value)} className="bg-[#0a1428] border border-[#1e2328] text-[#c8aa6e] px-4 py-2 rounded focus:border-[#c8aa6e] outline-none text-xs font-bold uppercase tracking-widest">
              {roles.map(role => <option key={role} value={role}>{role}</option>)}
            </select>
          </div>
          <div className="flex flex-col gap-1.5">
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest px-1">Sort by</span>
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} className="bg-[#0a1428] border border-[#1e2328] text-[#c8aa6e] px-4 py-2 rounded focus:border-[#c8aa6e] outline-none text-xs font-bold uppercase tracking-widest">
              <option value="name-asc">Name (A-Z)</option>
              <option value="name-desc">Name (Z-A)</option>
              <option value="difficulty-asc">Difficulty (Low-High)</option>
              <option value="difficulty-desc">Difficulty (High-Low)</option>
            </select>
          </div>
        </div>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {filteredAndSortedChampions.map((champ, i) => (
          <div key={i} className="bg-[#0a1428] border border-[#1e2328] hover:border-[#c8aa6e]/50 transition-all rounded overflow-hidden group shadow-xl">
            <div className="aspect-square bg-gray-900 overflow-hidden relative">
              <img src={champ.iconUrl || `https://picsum.photos/seed/${champ.name}/400/400`} alt={champ.name} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" />
              <div className="absolute inset-0 bg-gradient-to-t from-[#0a1428] to-transparent opacity-60"></div>
              <div className="absolute bottom-4 left-4">
                <div className="text-white font-bold text-xl uppercase italic tracking-tighter">{champ.name}</div>
                <div className="text-[#c8aa6e] text-xs font-bold uppercase tracking-widest">{champ.role}</div>
              </div>
            </div>
            <div className="p-4">
              <p className="text-gray-400 text-xs line-clamp-2 mb-3 h-8">{champ.description}</p>
              <div className="flex justify-between items-center">
                <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Difficulty: {champ.difficulty}</span>
                <button onClick={() => setSelectedChamp(champ.name)} className="text-[#c8aa6e] text-[10px] font-bold uppercase hover:text-white transition-colors underline underline-offset-4 tracking-widest">Explore</button>
              </div>
            </div>
          </div>
        ))}
      </div>
      {selectedChamp && <ChampionDetailsModal championName={selectedChamp} onClose={() => setSelectedChamp(null)} />}
    </div>
  );
};

const ItemsPage = () => {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    geminiService.getItems().then(data => {
      setItems(data);
      setLoading(false);
    });
  }, []);

  const filteredItems = useMemo(() => {
    return items.filter(i => i.name.toLowerCase().includes(search.toLowerCase()));
  }, [items, search]);

  if (loading) return <div className="p-20 text-center text-[#c8aa6e] animate-pulse font-bold uppercase tracking-[0.2em]">Stocking Item Shop...</div>;

  return (
    <div className="max-w-7xl mx-auto px-4 py-12">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
        <div>
          <h1 className="lol-font text-5xl text-[#c8aa6e] uppercase tracking-tighter mb-2 italic">Item Shop</h1>
          <p className="text-gray-500 text-sm font-bold uppercase tracking-widest italic">The Arsenal of the Rift</p>
        </div>
        <div className="relative w-full md:w-80">
          <input 
            type="text" 
            placeholder="Search Items..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-[#0a1428] border border-[#1e2328] text-white px-4 py-2 rounded focus:border-[#c8aa6e] outline-none text-xs font-bold"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredItems.map((item, i) => (
          <div key={i} className="bg-[#0a1428] border border-[#1e2328] hover:border-[#c8aa6e]/30 transition-all rounded p-5 group flex gap-5">
            <div className="w-20 h-20 bg-gray-900 border border-[#3c3c41] rounded p-1 group-hover:border-[#c8aa6e] transition-colors shrink-0">
               <img src={item.iconUrl || `https://picsum.photos/seed/${item.name}/120/120`} alt={item.name} className="w-full h-full object-cover" />
            </div>
            <div className="flex flex-col flex-grow">
               <div className="flex justify-between items-start mb-1">
                  <h3 className="text-[#c8aa6e] font-black italic uppercase text-lg tracking-tighter">{item.name}</h3>
                  <div className="flex items-center gap-1.5 bg-yellow-900/10 border border-yellow-900/30 px-2 py-0.5 rounded">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                    <span className="text-yellow-500 font-bold text-xs">{item.gold}</span>
                  </div>
               </div>
               <p className="text-blue-400 text-[10px] font-bold italic mb-2 tracking-tight">{item.stats}</p>
               <p className="text-gray-400 text-xs leading-relaxed line-clamp-2">{item.description}</p>
               <div className="mt-auto pt-3 flex gap-1">
                 {item.tags.map(tag => (
                   <span key={tag} className="text-[8px] bg-[#1e2328] text-gray-500 px-2 py-0.5 rounded border border-[#3c3c41] uppercase font-bold">{tag}</span>
                 ))}
               </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const ProfilePage = () => {
  const [player, setPlayer] = useState<PlayerSummary | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    const fetchPlayer = async () => {
      const parts = window.location.hash.split('/');
      const region = parts[2];
      const name = decodeURIComponent(parts[3] || '');
      if (!name) return;
      try {
        setLoading(true);
        const [profileData, matchData] = await Promise.all([geminiService.searchPlayer(name, region), geminiService.getMatchHistory(name)]);
        setPlayer(profileData);
        setMatches(matchData);
        setError(null);
      } catch (err) { setError("Could not find the requested summoner."); } finally { setLoading(false); }
    };
    fetchPlayer();
  }, [window.location.hash]);
  if (loading) return <div className="max-w-7xl mx-auto px-4 py-32 flex flex-col items-center justify-center space-y-4"><div className="w-20 h-20 border-4 border-[#c8aa6e]/20 border-t-[#c8aa6e] rounded-full animate-spin"></div><p className="text-[#c8aa6e] font-bold uppercase tracking-widest animate-pulse">Syncing with Rift...</p></div>;
  if (error || !player) return <div className="max-w-7xl mx-auto px-4 py-32 text-center"><h2 className="text-3xl font-bold text-red-500 mb-4 italic">SIGNAL LOST</h2><p className="text-gray-400 mb-8">{error || "Summoner not found in database."}</p><button onClick={() => window.location.hash = '#/'} className="bg-[#c8aa6e] text-[#0a1428] px-6 py-2 rounded font-bold uppercase tracking-widest italic active:scale-95 transition-all">Back to Terminal</button></div>;
  return ( <div className="max-w-7xl mx-auto px-4 py-8"><PlayerStats player={player} /><MatchHistory matches={matches} /></div> );
};

const App: React.FC = () => {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/champions" element={<ChampionsPage />} />
          <Route path="/items" element={<ItemsPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/profile/:region/:name" element={<ProfilePage />} />
        </Routes>
      </Layout>
    </Router>
  );
};

export default App;
