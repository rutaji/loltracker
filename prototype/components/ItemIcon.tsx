
import React, { useState, useRef, useEffect } from 'react';
import { geminiService } from '../services/geminiService';
import { Item } from '../types';

interface ItemIconProps {
  itemName: string;
  size?: 'sm' | 'md';
}

const ItemIcon: React.FC<ItemIconProps> = ({ itemName, size = 'md' }) => {
  const [isHovered, setIsHovered] = useState(false);
  const [details, setDetails] = useState<Item | null>(null);
  const [loading, setLoading] = useState(false);
  const timerRef = useRef<number | null>(null);

  const fetchDetails = async () => {
    if (details || loading) return;
    setLoading(true);
    try {
      const data = await geminiService.getItemDetails(itemName);
      setDetails(data);
    } catch (e) {
      console.error("Failed to load item details", e);
    } finally {
      setLoading(false);
    }
  };

  const handleMouseEnter = () => {
    timerRef.current = window.setTimeout(() => {
      setIsHovered(true);
      fetchDetails();
    }, 200);
  };

  const handleMouseLeave = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setIsHovered(false);
  };

  const sizeClasses = size === 'sm' ? 'w-5 h-5' : 'w-7 h-7';

  return (
    <div 
      className={`relative ${sizeClasses} bg-[#0a1428] border border-gray-800 rounded-sm group cursor-help`}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <img 
        src={`https://picsum.photos/seed/${itemName}/40/40`} 
        alt={itemName} 
        className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity"
      />
      
      {isHovered && (
        <div className="fixed z-[999] w-64 p-4 bg-[#0a1428] border border-[#c8aa6e]/50 rounded shadow-2xl pointer-events-none transform -translate-x-1/2 -translate-y-[120%] left-1/2 md:absolute md:left-auto md:right-0 md:translate-x-0 md:-translate-y-[110%] md:w-72 animate-fadeIn backdrop-blur-md">
          <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 md:left-auto md:right-4 w-4 h-4 bg-[#0a1428] border-r border-b border-[#c8aa6e]/50 rotate-45"></div>
          
          {loading ? (
            <div className="flex items-center justify-center gap-2 py-4">
              <div className="w-4 h-4 border-2 border-[#c8aa6e] border-t-transparent rounded-full animate-spin"></div>
              <span className="text-[10px] text-[#c8aa6e] font-bold uppercase tracking-widest italic">Decrypting Item...</span>
            </div>
          ) : details ? (
            <div className="space-y-2">
              <div className="flex justify-between items-start border-b border-[#1e2328] pb-2">
                <div>
                  <h4 className="text-[#c8aa6e] font-black italic uppercase text-xs tracking-tighter">{details.name}</h4>
                  <div className="flex gap-1 mt-1">
                    {details.tags.slice(0, 2).map(tag => (
                      <span key={tag} className="text-[8px] bg-gray-900 text-gray-500 px-1 py-0.5 rounded border border-gray-800 uppercase font-bold">{tag}</span>
                    ))}
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-2.5 h-2.5 bg-yellow-500 rounded-full border border-yellow-300"></div>
                  <span className="text-yellow-500 font-bold text-[10px]">{details.gold}</span>
                </div>
              </div>
              
              <div className="text-[10px] text-blue-400 font-bold leading-tight italic py-1">
                {details.stats}
              </div>
              
              <div className="text-[10px] text-gray-400 leading-relaxed font-medium">
                {details.description}
              </div>
            </div>
          ) : (
             <div className="text-center py-2 text-[10px] text-gray-500 font-bold uppercase tracking-widest">{itemName}</div>
          )}
        </div>
      )}
    </div>
  );
};

export default ItemIcon;
