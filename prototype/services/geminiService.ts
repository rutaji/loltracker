
import { GoogleGenAI, Type } from "@google/genai";
import { PlayerSummary, Match, Item } from "../types";

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
  }
};
