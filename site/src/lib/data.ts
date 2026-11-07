import raw from '../data/cookies.json';

export interface Cookie {
  slug: string;
  name: string;
  rarity: string;
  image: string;
  backstory: string;
  personality: string;
  personalityTags: string[];
  wikiUrl: string;
}

export const cookies = raw.cookies as Cookie[];
export const rarityOrder = (raw.rarityOrder as string[]).filter((r) =>
  cookies.some((c) => c.rarity === r),
);
export const tags = (raw.tags as string[]).filter((t) =>
  cookies.some((c) => c.personalityTags.includes(t)),
);

export const rarityLabel = (r: string) =>
  r.split('-').map((w) => w[0].toUpperCase() + w.slice(1)).join(' ');

export const tagSlug = (t: string) => t.toLowerCase();

export const byRarity = rarityOrder.map((r) => ({
  rarity: r,
  cookies: cookies.filter((c) => c.rarity === r),
}));
