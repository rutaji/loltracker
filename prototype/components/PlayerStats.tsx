
import React from 'react';
import { PlayerSummary } from '../types';

interface PlayerStatsProps {
  player: PlayerSummary;
}

const PlayerStats: React.FC<PlayerStatsProps> = ({ player }) => {
  return (
    <div className="flex flex-col gap-6">
      {/* Profile Header */}
      <div className="bg-[#0a1428] border border-[#1e2328] rounded p-6 flex flex-col md:flex-row items-center gap-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 blur-[100px] rounded-full -mr-20 -mt-20"></div>
        
        <div className="relative">
          <div className="w-24 h-24 rounded border-2 border-[#c8aa6e] p-0.5 overflow-hidden">
            <img 
              src={player.profileIconUrl || `https://picsum.photos/seed/${player.name}/200/200`} 
              alt="Profile Icon" 
              className="w-full h-full object-cover"
            />
          </div>
          <div className="absolute -bottom-2 -right-2 bg-[#1e2328] border border-[#c8aa6e] px-2 py-0.5 rounded text-xs font-bold text-[#c8aa6e]">
            {player.level}
          </div>
        </div>

        <div className="flex-grow text-center md:text-left">
          <div className="flex items-baseline gap-2 justify-center md:justify-start">
            <h1 className="text-3xl font-bold tracking-tight text-white">{player.name}</h1>
            <span className="text-gray-500 text-lg">#{player.tag}</span>
          </div>
          <div className="text-gray-400 mt-1 uppercase text-xs tracking-widest font-semibold">{player.region}</div>
          <div className="mt-4 flex flex-wrap gap-2 justify-center md:justify-start">
            <span className="bg-blue-900/30 text-blue-400 px-3 py-1 rounded-full text-xs font-bold border border-blue-900/50">Top Laner</span>
            <span className="bg-purple-900/30 text-purple-400 px-3 py-1 rounded-full text-xs font-bold border border-purple-900/50">Tactician</span>
          </div>
        </div>

        <div className="flex flex-col items-center md:items-end gap-2 border-t md:border-t-0 md:border-l border-[#1e2328] pt-4 md:pt-0 md:pl-8">
           <div className="text-xs text-gray-500 uppercase font-bold">Current Rank</div>
           <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="text-[#c8aa6e] font-bold text-xl uppercase italic">{player.rank.tier} {player.rank.rank}</div>
                <div className="text-gray-400 text-sm">{player.rank.lp} LP</div>
              </div>
              <div className="w-12 h-12 flex items-center justify-center">
                 {/* Mock Rank Icon */}
                 <div className={`w-full h-full rounded-full border-2 border-[#c8aa6e] shadow-[0_0_10px_rgba(200,170,110,0.3)] flex items-center justify-center bg-gradient-to-tr from-[#1e2328] to-[#2a2f35]`}>
                    <span className="text-[#c8aa6e] text-xs font-bold">{player.rank.tier[0]}</span>
                 </div>
              </div>
           </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Win Rate Stats */}
        <div className="bg-[#0a1428] border border-[#1e2328] rounded p-5 flex flex-col justify-between">
          <div>
            <h3 className="text-gray-400 text-xs font-bold uppercase mb-4 tracking-wider">Ranked Performance</h3>
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-300 text-sm">Overall Win Rate</span>
              <span className="text-white font-bold">{player.rank.winRate}%</span>
            </div>
            <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden mb-4">
              <div 
                className="h-full bg-blue-500 transition-all" 
                style={{ width: `${player.rank.winRate}%` }}
              ></div>
            </div>
            <div className="flex justify-between text-xs text-gray-500">
              <span>{player.rank.wins} Wins</span>
              <span>{player.rank.losses} Losses</span>
            </div>
          </div>
          
          <div className="mt-6 pt-6 border-t border-[#1e2328] flex items-center justify-between">
            <span className="text-gray-400 text-xs font-bold uppercase tracking-wider">Average KDA</span>
            <span className="text-2xl font-black text-white italic">{player.avgKda}</span>
          </div>
        </div>

        {/* Top Champions */}
        <div className="bg-[#0a1428] border border-[#1e2328] rounded p-5 md:col-span-2">
          <h3 className="text-gray-400 text-xs font-bold uppercase mb-4 tracking-wider">Most Played Champions</h3>
          <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-thin">
            {player.topChampions.map((champ, idx) => (
              <div key={idx} className="flex flex-col items-center min-w-[100px] group cursor-pointer">
                <div className="w-12 h-12 rounded-full border border-[#1e2328] group-hover:border-[#c8aa6e] transition-colors overflow-hidden mb-2">
                  <img src={champ.iconUrl || `https://picsum.photos/seed/${champ.name}/100/100`} alt={champ.name} className="w-full h-full object-cover" />
                </div>
                <div className="text-white text-xs font-bold truncate w-full text-center">{champ.name}</div>
                <div className="text-gray-500 text-[10px]">Lvl {champ.level}</div>
                <div className="text-[#c8aa6e] text-[10px] font-medium">{(champ.points / 1000).toFixed(1)}k pts</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlayerStats;
