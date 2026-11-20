// Static card data for the economy (shop, tier-page reward preview): the per-rarity order, Super Epic topics and card
// names. Fetched by the pages that need it, so it is not inlined into every tier page.
import type { APIRoute } from 'astro';
import { economyData } from '../../lib/train';

export const GET: APIRoute = () =>
  new Response(JSON.stringify(economyData()), { headers: { 'Content-Type': 'application/json' } });
