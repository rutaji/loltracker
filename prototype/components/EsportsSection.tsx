
import React, { useState } from 'react';
import { EsportsMatch, Standing, Participant } from '../types';
import { Icons } from '../constants';
import ItemIcon from './ItemIcon';

interface EsportsSectionProps {
  matches: EsportsMatch[];
  standings: Standing[];
}

const EsportsSection: React.FC<EsportsSectionProps> = ({ matches, standings }) => {
  const [expandedMatchId, setExpandedMatchId] = useState<string | null>(null);

  const toggleExpand = (id: string) => {
    setExpandedMatchId(expandedMatchId === id ? null : id);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-12">
      <div className="lg:col-span-2 space-y-6">
        <div className="flex items-center gap-2 mb-4">
          <Icons.Calendar />
          <h2 className="text-xl font-bold text-white tracking-tight uppercase">Pro Schedule</h2>
        </div>
        
        <div className="grid grid-cols-1 gap-4">
          {matches.map((match) => (
            <div key={match.id} className="bg-[#0a1428] border border-[#1e2328] rounded overflow-hidden group hover:border-[#c8aa6e]/50 transition-all shadow-xl">
              <div 
                onClick={() => toggleExpand(match.id)}
                className="p-4 flex flex-col sm:flex-row items-center justify-between gap-4 cursor-pointer"
              >
                <div className="flex items-center gap-2">
                  <span className="bg-yellow-900/20 text-[#c8aa6e] text-[10px] font-bold px-2 py-0.5 rounded border border-yellow-900/50 uppercase tracking-widest">
                    {match.league}
                  </span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-widest ${
                    match.status === 'live' ? 'bg-red-900/20 text-red-500 border-red-900/50 animate-pulse' : 'bg-gray-800 text-gray-400 border-gray-700'
                  }`}>
                    {match.status}
                  </span>
                </div>

                <div className="flex items-center gap-6 flex-grow justify-center">
                  <div className="flex flex-col items-center gap-1 w-24 text-center">
                    <div className="w-12 h-12 bg-gray-900 rounded-full flex items-center justify-center overflow-hidden border border-gray-700 group-hover:border-[#c8aa6e]/50 transition-colors shadow-inner">
                      <img src={match.teamA.logo || `https://picsum.photos/seed/${match.teamA.name}/120/120`} alt="" className="w-full h-full object-cover" />
                    </div>
                    <span className="text-white text-[10px] font-black uppercase tracking-tighter truncate w-full italic">{match.teamA.name}</span>
                  </div>

                  <div className="flex flex-col items-center">
                    <div className="text-2xl font-black text-white italic tracking-tighter">
                      {match.status === 'upcoming' ? 'VS' : `${match.teamA.score} - ${match.teamB.score}`}
                    </div>
                    <div className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">{match.timestamp}</div>
                  </div>

                  <div className="flex flex-col items-center gap-1 w-24 text-center">
                    <div className="w-12 h-12 bg-gray-900 rounded-full flex items-center justify-center overflow-hidden border border-gray-700 group-hover:border-[#c8aa6e]/50 transition-colors shadow-inner">
                      <img src={match.teamB.logo || `https://picsum.photos/seed/${match.teamB.name}/120/120`} alt="" className="w-full h-full object-cover" />
                    </div>
                    <span className="text-white text-[10px] font-black uppercase tracking-tighter truncate w-full italic">{match.teamB.name}</span>
                  </div>
                </div>

                <div className="flex items-center">
                   <svg 
                      className={`w-6 h-6 text-[#c8aa6e] transition-transform ${expandedMatchId === match.id ? 'rotate-180' : ''}`}
                      fill="none" stroke="currentColor" viewBox="0 0 24 24"
                   >
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                   </svg>
                </div>
              </div>

              {expandedMatchId === match.id && match.matchDetails && (
                <div className="bg-[#010a13] border-t border-[#1e2328] p-6 animate-fadeIn">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Blue Side */}
                    <div className="space-y-3">
                       <div className="flex items-center justify-between border-b border-blue-900/30 pb-2 mb-2">
                          <span className="text-[10px] font-black text-blue-400 uppercase tracking-[0.2em] italic">Blue Side Organizations</span>
                          <span className="text-[8px] text-gray-500 font-bold">KDA / ITEMS</span>
                       </div>
                       {match.matchDetails.participants.slice(0, 5).map((p, i) => (
                         <ProScoreboardRow key={i} participant={p} side="blue" />
                       ))}
                    </div>
                    {/* Red Side */}
                    <div className="space-y-3">
                       <div className="flex items-center justify-between border-b border-red-900/30 pb-2 mb-2 flex-row-reverse">
                          <span className="text-[10px] font-black text-red-400 uppercase tracking-[0.2em] italic">Red Side Organizations</span>
                          <span className="text-[8px] text-gray-500 font-bold text-right uppercase tracking-widest">KDA / ITEMS</span>
                       </div>
                       {match.matchDetails.participants.slice(5, 10).map((p, i) => (
                         <ProScoreboardRow key={i} participant={p} side="red" />
                       ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-6">
        <div className="flex items-center gap-2 mb-4">
          <Icons.Trophy />
          <h2 className="text-xl font-bold text-white tracking-tight uppercase">Standings</h2>
        </div>

        <div className="bg-[#0a1428] border border-[#1e2328] rounded overflow-hidden shadow-2xl">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#1e2328] text-gray-400 font-bold uppercase tracking-wider">
              <tr>
                <th className="px-4 py-3 italic">Rank</th>
                <th className="px-4 py-3">Team</th>
                <th className="px-4 py-3 text-right">W - L</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e2328]">
              {standings.map((team, idx) => (
                <tr key={idx} className="hover:bg-[#1e2328]/50 transition-colors group cursor-default">
                  <td className="px-4 py-4 text-[#c8aa6e] font-black italic text-sm">#{team.rank}</td>
                  <td className="px-4 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-gray-900 rounded-full overflow-hidden border border-gray-700 group-hover:border-[#c8aa6e]/50 transition-colors shadow-inner p-1">
                        <img src={team.logo || `https://picsum.photos/seed/${team.teamName}/60/60`} alt="" className="w-full h-full object-contain" />
                      </div>
                      <span className="text-white font-black uppercase tracking-tighter italic group-hover:text-[#c8aa6e] transition-colors">{team.teamName}</span>
                    </div>
                  </td>
                  <td className="px-4 py-4 text-right text-gray-400 font-black italic tracking-tighter">
                    {team.wins} - {team.losses}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="p-4 bg-[#1e2328]/50 text-center border-t border-[#0a1428]">
            <button className="text-[#c8aa6e] text-[10px] font-black uppercase tracking-[0.2em] hover:text-white transition-colors italic">
              View Extended Leaderboards
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const ProScoreboardRow: React.FC<{ participant: Participant, side: 'blue' | 'red' }> = ({ participant, side }) => (
  <div className={`flex items-center gap-4 p-2 rounded bg-[#0a1428] border border-[#1e2328] hover:border-[#3c3c41] transition-all group ${side === 'red' ? 'flex-row-reverse' : ''}`}>
    <div className="w-10 h-10 rounded bg-gray-900 overflow-hidden shrink-0 border border-[#3c3c41] group-hover:border-[#c8aa6e]/40 transition-colors">
      <img src={participant.championIcon || `https://picsum.photos/seed/${participant.championName}/60/60`} className="w-full h-full object-cover grayscale-[0.2] group-hover:grayscale-0" alt="" />
    </div>
    
    <div className={`flex flex-col flex-grow overflow-hidden ${side === 'red' ? 'text-right' : ''}`}>
       <div className="text-[11px] text-white font-black uppercase tracking-tighter italic truncate">{participant.summonerName}</div>
       <div className="text-[8px] text-[#c8aa6e] font-bold uppercase tracking-widest italic">{participant.championName}</div>
    </div>

    <div className={`flex flex-col items-center gap-1 ${side === 'red' ? 'mr-2' : 'ml-2'}`}>
      <div className="text-[10px] font-black text-gray-300 w-16 text-center tracking-tighter italic">
        {participant.kills}/{participant.deaths}/{participant.assists}
      </div>
      <div className={`flex gap-0.5 ${side === 'red' ? 'flex-row-reverse' : ''}`}>
         {participant.items.map((item, i) => (
           <ItemIcon key={i} itemName={item} size="sm" />
         ))}
         {Array.from({ length: Math.max(0, 6 - participant.items.length) }).map((_, i) => (
           <div key={i} className="w-4 h-4 bg-[#010a13] border border-gray-900/50 rounded-[1px]"></div>
         ))}
      </div>
    </div>
  </div>
);

export default EsportsSection;
