// Static JSON for each question bank, fetched by the quiz page only when it is needed.
import type { APIRoute } from 'astro';
import { banks } from '../../../lib/train';

export function getStaticPaths() {
  return banks.map((b) => ({ params: { topic: b.topic }, props: { questions: b.questions } }));
}

export const GET: APIRoute = ({ props }) =>
  new Response(JSON.stringify(props.questions), { headers: { 'Content-Type': 'application/json' } });
