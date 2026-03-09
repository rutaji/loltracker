
import React, { useState } from 'react';
import { Match, Participant } from '../types';
import ItemIcon from './ItemIcon';

interface MatchHistoryProps {
  matches: Match[];
}

const MatchHistory: React.FC<MatchHistoryProps> = ({ matches }) => {
  const [expandedMatchId, setExpandedMatchId] = useState<string | null>(null);

  const toggleMatch = (id: string) => {
    setExpandedMatchId(expandedMatchId === id ? null : id);
  };

  return (
    <div className="flex flex-col gap-4 mt-8">
      <div className="flex items-center justify-between px-2">
        <h2 className="text-xl font-bold text-white tracking-tight italic uppercase border-l-4 border-[#c8aa6e] pl-4">Recent Matches</h2>
        <div className="flex gap-2">
          <button className="bg-[#1e2328] text-xs px-3 py-1 rounded border border-[#3c3c41] text-gray-300 hover:text-white">All</button>
          <button className="bg-[#1e2328] text-xs px-3 py-1 rounded border border-[#3c3c41] text-gray-300 hover:text-white">Ranked</button>
        </div>
      </div>

      {matches.map((match) => (
        <div key={match.id} className="flex flex-col border border-[#1e2328] rounded overflow-hidden shadow-lg">
          {/* Collapsed View */}
          <div 
            onClick={() => toggleMatch(match.id)}
            className={`flex flex-col md:flex-row items-center p-4 cursor-pointer transition-all hover:bg-[#1e2328]/50 border-l-4 ${
              match.isWin ? 'border-blue-500 bg-blue-500/5' : 'border-red-500 bg-red-500/5'
            }`}
          >
            <div className="flex items-center gap-4 w-full md:w-auto md:min-w-[150px]">
              <div className="flex flex-col">
                <span className={`font-bold text-sm uppercase tracking-wider ${match.isWin ? 'text-blue-400' : 'text-red-400'}`}>
                  {match.isWin ? 'Victory' : 'Defeat'}
                </span>
                <span className="text-gray-500 text-[10px] font-bold uppercase">{match.gameMode}</span>
                <span className="text-gray-500 text-[10px] mt-1">{match.creationDate}</span>
              </div>
            </div>

            <div className="flex items-center gap-4 flex-grow justify-start w-full md:w-auto mt-4 md:mt-0">
               <div className="relative">
                  <img 
                    src={match.participants[0].championIcon || `https://picsum.photos/seed/${match.participants[0].championName}/100/100`} 
                    alt="Champ" 
                    className="w-12 h-12 rounded border border-[#c8aa6e]/30 shadow-md"
                  />
                  <div className="absolute -bottom-1 -right-1 bg-[#0a1428] text-[8px] text-[#c8aa6e] px-1 rounded border border-[#c8aa6e]/50 font-bold">18</div>
               </div>

               <div className="flex flex-col min-w-[100px]">
                  <div className="text-white font-black text-lg italic tracking-tighter">
                    {match.participants[0].kills} / <span className="text-red-500">{match.participants[0].deaths}</span> / {match.participants[0].assists}
                  </div>
                  <div className="text-gray-400 text-[10px] font-bold uppercase">
                    {((match.participants[0].kills + match.participants[0].assists) / (match.participants[0].deaths || 1)).toFixed(2)} KDA
                  </div>
               </div>

               <div className="grid grid-cols-4 sm:grid-cols-7 gap-1 ml-4">
                  {match.participants[0].items.map((item, i) => (
                    <ItemIcon key={i} itemName={item} />
                  ))}
                  {/* Empty slots */}
                  {Array.from({ length: Math.max(0, 7 - match.participants[0].items.length) }).map((_, i) => (
                    <div key={`empty-${i}`} className="w-7 h-7 bg-[#010a13] border border-gray-900/50 rounded-sm"></div>
                  ))}
               </div>
            </div>

            <div className="hidden lg:flex items-center gap-4 ml-6">
               <div className="flex flex-col gap-1">
                  {match.participants.slice(0, 5).map((p, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded-sm bg-gray-800 border border-gray-700">
                         <img src={`https://picsum.photos/seed/${p.championName}/20/20`} className="w-full h-full object-cover" alt="" />
                      </div>
                      <span className="text-[10px] text-gray-400 font-medium truncate w-24 group-hover:text-white">{p.summonerName}</span>
                    </div>
                  ))}
               </div>
               <div className="flex flex-col gap-1">
                  {match.participants.slice(5, 10).map((p, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded-sm bg-gray-800 border border-gray-700">
                         <img src={`https://picsum.photos/seed/${p.championName}/20/20`} className="w-full h-full object-cover" alt="" />
                      </div>
                      <span className="text-[10px] text-gray-400 font-medium truncate w-24 group-hover:text-white">{p.summonerName}</span>
                    </div>
                  ))}
               </div>
            </div>

            <div className="ml-auto p-2">
               <svg 
                  className={`w-5 h-5 text-[#c8aa6e] transition-transform ${expandedMatchId === match.id ? 'rotate-180' : ''}`}
                  fill="none" stroke="currentColor" viewBox="0 0 24 24"
               >
                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
               </svg>
            </div>
          </div>

          {/* Expanded View */}
          {expandedMatchId === match.id && (
            <div className="bg-[#0a1428] border-t border-[#1e2328] p-4 animate-fadeIn">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                 {/* Team 1 */}
                 <div className="flex flex-col gap-2">
                    <div className="flex items-center justify-between px-3 bg-blue-900/10 py-2 rounded border border-blue-900/20">
                      <span className="text-blue-400 font-black italic text-xs uppercase tracking-widest">Blue Team</span>
                      <span className="text-gray-500 text-[10px] font-bold uppercase tracking-widest">
                        Towers: {match.teams[0].objectives.tower} | Barons: {match.teams[0].objectives.baron} | Dragons: {match.teams[0].objectives.dragon}
                      </span>
                    </div>
                    <div className="space-y-1">
                      {match.participants.filter(p => p.teamId === 100).map((p, i) => (
                        <ScoreboardRow key={i} participant={p} />
                      ))}
                    </div>
                 </div>
                 {/* Team 2 */}
                 <div className="flex flex-col gap-2">
                    <div className="flex items-center justify-between px-3 bg-red-900/10 py-2 rounded border border-red-900/20">
                      <span className="text-red-400 font-black italic text-xs uppercase tracking-widest">Red Team</span>
                      <span className="text-gray-500 text-[10px] font-bold uppercase tracking-widest text-right">
                        Towers: {match.teams[1].objectives.tower} | Barons: {match.teams[1].objectives.baron} | Dragons: {match.teams[1].objectives.dragon}
                      </span>
                    </div>
                    <div className="space-y-1">
                      {match.participants.filter(p => p.teamId === 200).map((p, i) => (
                        <ScoreboardRow key={i} participant={p} />
                      ))}
                    </div>
                 </div>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

const ScoreboardRow: React.FC<{ participant: Participant }> = ({ participant }) => (
  <div className="flex items-center gap-3 p-2 hover:bg-[#1e2328] rounded transition-all border border-transparent hover:border-[#3c3c41] group">
    <div className="w-10 h-10 rounded border border-[#3c3c41] bg-gray-900 overflow-hidden shrink-0 group-hover:border-[#c8aa6e]/50">
       <img src={participant.championIcon || `https://picsum.photos/seed/${participant.championName}/60/60`} className="w-full h-full object-cover" alt="" />
    </div>
    <div className="flex flex-col w-28 shrink-0 overflow-hidden">
       <div className="text-[10px] text-white font-black uppercase tracking-tighter truncate italic">{participant.summonerName}</div>
       <div className="text-[8px] text-[#c8aa6e] uppercase font-bold tracking-widest">{participant.championName}</div>
    </div>
    <div className="flex-grow flex items-center justify-between gap-4">
       <div className="text-[10px] font-black text-gray-300 w-20 text-center italic">
         {participant.kills} / <span className="text-red-500">{participant.deaths}</span> / {participant.assists}
       </div>
       <div className="hidden sm:flex gap-1 shrink-0">
         {participant.items.map((item, i) => (
           <ItemIcon key={i} itemName={item} size="sm" />
         ))}
         {Array.from({ length: Math.max(0, 6 - participant.items.length) }).map((_, i) => (
           <div key={i} className="w-5 h-5 bg-[#010a13] border border-gray-900 rounded-sm"></div>
         ))}
       </div>
    </div>
    <div className="text-[10px] text-gray-500 w-16 text-right font-bold uppercase tracking-tighter">{participant.cs} CS</div>
  </div>
);

export default MatchHistory;
