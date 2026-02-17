
import { GoogleGenAI, Type } from "@google/genai";
import { PlayerSummary, Match, EsportsMatch, Standing, ProTeam, Item } from "../types";

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY || "" });

export const geminiService = {
  async searchPlayer(name: string, region: string): Promise<PlayerSummary> {
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: `Search for a League of Legends player named "${name}" in region "${region}". Generate a realistic profile. Include an "avgKda" string like "4.21:1".`,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            name: { type: Type.STRING },
            tag: { type: Type.STRING },
            region: { type: Type.STRING },
            level: { type: Type.NUMBER },
            profileIconUrl: { type: Type.STRING },
            avgKda: { type: Type.STRING },
            rank: {
              type: Type.OBJECT,
              properties: {
                tier: { type: Type.STRING },
                rank: { type: Type.STRING },
                lp: { type: Type.NUMBER },
                wins: { type: Type.NUMBER },
                losses: { type: Type.NUMBER },
                winRate: { type: Type.NUMBER },
              },
              required: ["tier", "rank", "lp", "wins", "losses", "winRate"]
            },
            topChampions: {
              type: Type.ARRAY,
              items: {
                type: Type.OBJECT,
                properties: {
                  name: { type: Type.STRING },
                  level: { type: Type.NUMBER },
                  points: { type: Type.NUMBER },
                  iconUrl: { type: Type.STRING },
                },
                required: ["name", "level", "points", "iconUrl"]
              }
            }
          },
          required: ["name", "tag", "region", "level", "profileIconUrl", "avgKda", "rank", "topChampions"]
        },
      },
    });

    return JSON.parse(response.text);
  },

  async getMatchHistory(playerName: string): Promise<Match[]> {
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: `Generate 5 detailed recent League of Legends matches for ${playerName}.`,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.ARRAY,
          items: {
            type: Type.OBJECT,
            properties: {
              id: { type: Type.STRING },
              gameMode: { type: Type.STRING },
              duration: { type: Type.STRING },
              creationDate: { type: Type.STRING },
              isWin: { type: Type.BOOLEAN },
              participants: {
                type: Type.ARRAY,
                items: {
                  type: Type.OBJECT,
                  properties: {
                    summonerName: { type: Type.STRING },
                    championName: { type: Type.STRING },
                    championIcon: { type: Type.STRING },
                    role: { type: Type.STRING },
                    kills: { type: Type.NUMBER },
                    deaths: { type: Type.NUMBER },
                    assists: { type: Type.NUMBER },
                    cs: { type: Type.NUMBER },
                    gold: { type: Type.NUMBER },
                    damage: { type: Type.NUMBER },
                    items: { type: Type.ARRAY, items: { type: Type.STRING } },
                    teamId: { type: Type.NUMBER },
                    win: { type: Type.BOOLEAN }
                  },
                  required: ["summonerName", "championName", "championIcon", "role", "kills", "deaths", "assists", "cs", "gold", "damage", "items", "teamId", "win"]
                }
              },
              teams: {
                type: Type.ARRAY,
                items: {
                  type: Type.OBJECT,
                  properties: {
                    teamId: { type: Type.NUMBER },
                    win: { type: Type.BOOLEAN },
                    kills: { type: Type.NUMBER },
                    gold: { type: Type.NUMBER },
                    objectives: {
                      type: Type.OBJECT,
                      properties: {
                        baron: { type: Type.NUMBER },
                        dragon: { type: Type.NUMBER },
                        tower: { type: Type.NUMBER }
                      },
                      required: ["baron", "dragon", "tower"]
                    }
                  },
                  required: ["teamId", "win", "kills", "gold", "objectives"]
                }
              }
            },
            required: ["id", "gameMode", "duration", "creationDate", "isWin", "participants", "teams"]
          }
        },
      },
    });

    return JSON.parse(response.text);
  },

  async getEsportsData(): Promise<{ matches: EsportsMatch[]; standings: Standing[] }> {
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: "Generate current League of Legends esports information including 4 matches (with detailed matchDetails for expansion) and top 5 standings.",
      config: {
        thinkingConfig: { thinkingBudget: 1000 },
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            matches: {
              type: Type.ARRAY,
              items: {
                type: Type.OBJECT,
                properties: {
                  id: { type: Type.STRING },
                  league: { type: Type.STRING },
                  teamA: {
                    type: Type.OBJECT,
                    properties: { name: { type: Type.STRING }, logo: { type: Type.STRING }, score: { type: Type.NUMBER } },
                    required: ["name", "logo", "score"]
                  },
                  teamB: {
                    type: Type.OBJECT,
                    properties: { name: { type: Type.STRING }, logo: { type: Type.STRING }, score: { type: Type.NUMBER } },
                    required: ["name", "logo", "score"]
                  },
                  status: { type: Type.STRING },
                  timestamp: { type: Type.STRING },
                  matchDetails: {
                    type: Type.OBJECT,
                    properties: {
                       participants: {
                          type: Type.ARRAY,
                          items: {
                            type: Type.OBJECT,
                            properties: {
                              summonerName: { type: Type.STRING },
                              championName: { type: Type.STRING },
                              championIcon: { type: Type.STRING },
                              role: { type: Type.STRING },
                              kills: { type: Type.NUMBER },
                              deaths: { type: Type.NUMBER },
                              assists: { type: Type.NUMBER },
                              cs: { type: Type.NUMBER },
                              gold: { type: Type.NUMBER },
                              damage: { type: Type.NUMBER },
                              items: { type: Type.ARRAY, items: { type: Type.STRING } },
                              teamId: { type: Type.NUMBER },
                              win: { type: Type.BOOLEAN }
                            },
                            required: ["summonerName", "championName", "championIcon", "role", "kills", "deaths", "assists", "cs", "gold", "damage", "items", "teamId", "win"]
                          }
                       }
                    },
                    required: ["participants"]
                  }
                },
                required: ["id", "league", "teamA", "teamB", "status", "timestamp"]
              }
            },
            standings: {
              type: Type.ARRAY,
              items: {
                type: Type.OBJECT,
                properties: {
                  teamName: { type: Type.STRING },
                  logo: { type: Type.STRING },
                  wins: { type: Type.NUMBER },
                  losses: { type: Type.NUMBER },
                  rank: { type: Type.NUMBER }
                },
                required: ["teamName", "logo", "wins", "losses", "rank"]
              }
            }
          },
          required: ["matches", "standings"]
        },
      },
    });

    return JSON.parse(response.text);
  },

  async getChampions(): Promise<any[]> {
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: "List 12 popular League of Legends champions with their roles and a brief description.",
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.ARRAY,
          items: {
            type: Type.OBJECT,
            properties: {
              name: { type: Type.STRING },
              role: { type: Type.STRING },
              difficulty: { type: Type.STRING },
              description: { type: Type.STRING },
              iconUrl: { type: Type.STRING }
            },
            required: ["name", "role", "difficulty", "description", "iconUrl"]
          }
        }
      }
    });
    return JSON.parse(response.text);
  },

  async getChampionDetails(championName: string): Promise<any> {
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: `Provide ability details and base stats for the League of Legends champion ${championName}. Include Passive, Q, W, E, R, and stats (HP, Mana, AD, Armor).`,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            name: { type: Type.STRING },
            stats: {
              type: Type.OBJECT,
              properties: {
                health: { type: Type.NUMBER },
                mana: { type: Type.NUMBER },
                attackDamage: { type: Type.NUMBER },
                armor: { type: Type.NUMBER }
              },
              required: ["health", "mana", "attackDamage", "armor"]
            },
            abilities: {
              type: Type.ARRAY,
              items: {
                type: Type.OBJECT,
                properties: {
                  key: { type: Type.STRING },
                  name: { type: Type.STRING },
                  description: { type: Type.STRING }
                },
                required: ["key", "name", "description"]
              }
            }
          },
          required: ["name", "stats", "abilities"]
        }
      }
    });
    return JSON.parse(response.text);
  },

  async getItems(): Promise<Item[]> {
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: "List 20 iconic and powerful League of Legends items with their stats and descriptions.",
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.ARRAY,
          items: {
            type: Type.OBJECT,
            properties: {
              name: { type: Type.STRING },
              description: { type: Type.STRING },
              gold: { type: Type.NUMBER },
              stats: { type: Type.STRING },
              iconUrl: { type: Type.STRING },
              tags: { type: Type.ARRAY, items: { type: Type.STRING } }
            },
            required: ["name", "description", "gold", "stats", "iconUrl", "tags"]
          }
        }
      }
    });
    return JSON.parse(response.text);
  },

  async getItemDetails(itemName: string): Promise<Item> {
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: `Provide details for the League of Legends item: ${itemName}.`,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            name: { type: Type.STRING },
            description: { type: Type.STRING },
            gold: { type: Type.NUMBER },
            stats: { type: Type.STRING },
            iconUrl: { type: Type.STRING },
            tags: { type: Type.ARRAY, items: { type: Type.STRING } }
          },
          required: ["name", "description", "gold", "stats", "iconUrl", "tags"]
        }
      }
    });
    return JSON.parse(response.text);
  },

  async getProTeams(): Promise<{ id: string, name: string }[]> {
     return [
       { id: 't1', name: 'T1' },
       { id: 'gen', name: 'Gen.G' },
       { id: 'g2', name: 'G2 Esports' },
       { id: 'fnc', name: 'Fnatic' },
       { id: 'c9', name: 'Cloud9' },
       { id: 'tl', name: 'Team Liquid' },
     ];
  },

  async getProTeamDetails(teamId: string): Promise<ProTeam> {
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: `Generate professional League of Legends team statistics, roster, and recent matches for team ID: ${teamId}.`,
      config: {
        thinkingConfig: { thinkingBudget: 1000 },
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            id: { type: Type.STRING },
            name: { type: Type.STRING },
            logo: { type: Type.STRING },
            region: { type: Type.STRING },
            stats: {
              type: Type.OBJECT,
              properties: {
                winRate: { type: Type.NUMBER },
                avgGoldDiffAt15: { type: Type.NUMBER },
                firstBloodRate: { type: Type.NUMBER },
                towerRate: { type: Type.NUMBER }
              },
              required: ["winRate", "avgGoldDiffAt15", "firstBloodRate", "towerRate"]
            },
            roster: {
              type: Type.ARRAY,
              items: {
                type: Type.OBJECT,
                properties: {
                  name: { type: Type.STRING },
                  realName: { type: Type.STRING },
                  role: { type: Type.STRING },
                  nationality: { type: Type.STRING },
                  imageUrl: { type: Type.STRING }
                },
                required: ["name", "realName", "role", "nationality", "imageUrl"]
              }
            },
            recentMatches: {
              type: Type.ARRAY,
              items: {
                type: Type.OBJECT,
                properties: {
                  id: { type: Type.STRING },
                  league: { type: Type.STRING },
                  teamA: {
                    type: Type.OBJECT,
                    properties: { name: { type: Type.STRING }, logo: { type: Type.STRING }, score: { type: Type.NUMBER } },
                    required: ["name", "logo", "score"]
                  },
                  teamB: {
                    type: Type.OBJECT,
                    properties: { name: { type: Type.STRING }, logo: { type: Type.STRING }, score: { type: Type.NUMBER } },
                    required: ["name", "logo", "score"]
                  },
                  status: { type: Type.STRING },
                  timestamp: { type: Type.STRING }
                },
                required: ["id", "league", "teamA", "teamB", "status", "timestamp"]
              }
            }
          },
          required: ["id", "name", "logo", "region", "stats", "roster", "recentMatches"]
        },
      },
    });
    return JSON.parse(response.text);
  },

  async getLeaderboard(region: string): Promise<any[]> {
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: `Generate a top 10 leaderboard for Challenger players in the ${region} region.`,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.ARRAY,
          items: {
            type: Type.OBJECT,
            properties: {
              rank: { type: Type.NUMBER },
              summonerName: { type: Type.STRING },
              lp: { type: Type.NUMBER },
              winRate: { type: Type.NUMBER },
              level: { type: Type.NUMBER }
            },
            required: ["rank", "summonerName", "lp", "winRate", "level"]
          }
        }
      }
    });
    return JSON.parse(response.text);
  }
};
