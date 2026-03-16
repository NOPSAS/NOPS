const KARTVERKET_BASE = 'https://ws.geonorge.no/eiendomsregister/v1';

export async function hentEiendomData(
  knr: string,
  gnr: string,
  bnr: string
): Promise<Record<string, unknown> | null> {
  try {
    const url = `${KARTVERKET_BASE}/eiendom/${knr}/${gnr}/${bnr}`;
    const res = await fetch(url, { next: { revalidate: 3600 } });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}
