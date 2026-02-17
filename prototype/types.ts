
export interface PlayerSummary {
  name: string;
  tag: string;
  region: string;
  level: number;
  profileIconUrl: string;
  avgKda: string;
  rank: {
    tier: string;
    rank: string;
    lp: number;
    wins: number;
    losses: number;
    winRate: number;
  };
  topChampions: Array<{
    name: string;
    level: number;
    points: number;
    iconUrl: string;
  }>;
}

export interface Participant {
  summonerName: string;
  championName: string;
  championIcon: string;
  role: string;
  kills: number;
  deaths: number;
  assists: number;
  cs: number;
  gold: number;
  damage: number;
  items: string[];
  teamId: number;
  win: boolean;
}

export interface Match {
  id: string;
  gameMode: string;
  duration: string;
  creationDate: string;
  isWin: boolean;
  participants: Participant[];
  teams: Array<{
    teamId: number;
    win: boolean;
    kills: number;
    gold: number;
    objectives: {
      baron: number;
      dragon: number;
      tower: number;
    };
  }>;
}

export interface EsportsMatch {
  id: string;
  league: string;
  teamA: {
    name: string;
    logo: string;
    score: number;
  };
  teamB: {
    name: string;
    logo: string;
    score: number;
  };
  status: 'upcoming' | 'live' | 'completed';
  timestamp: string;
  matchDetails?: Match;
}

export interface Standing {
  teamName: string;
  logo: string;
  wins: number;
  losses: number;
  rank: number;
}

export interface ChampionAbility {
  key: string; // P, Q, W, E, R
  name: string;
  description: string;
}

export interface ProPlayer {
  name: string;
  realName: string;
  role: 'TOP' | 'JUNGLE' | 'MID' | 'ADC' | 'SUPPORT';
  nationality: string;
  imageUrl: string;
}

export interface ProTeam {
  id: string;
  name: string;
  logo: string;
  region: string;
  stats: {
    winRate: number;
    avgGoldDiffAt15: number;
    firstBloodRate: number;
    towerRate: number;
  };
  roster: ProPlayer[];
  recentMatches: EsportsMatch[];
}

export interface Item {
  name: string;
  description: string;
  gold: number;
  stats: string;
  iconUrl: string;
  tags: string[];
}
