'use client';

import { useParams } from 'next/navigation';
import useSWR from 'swr';
import { getPlans } from '@/lib/api';
import { StructuredPlan } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ConfidenceIndicator } from '@/components/confidence-indicator';

function approvalStatusLabel(status: string | null): string {
  switch (status) {
    case 'VERIFIED_APPROVED': return 'Verifisert godkjent';
    case 'ASSUMED_APPROVED': return 'Antatt godkjent';
    case 'RECEIVED': return 'Mottatt';
    case 'UNKNOWN': return 'Ukjent';
    default: return status ?? '—';
  }
}

function approvalStatusVariant(status: string | null): 'success' | 'warning' | 'default' | 'secondary' {
  switch (status) {
    case 'VERIFIED_APPROVED': return 'success';
    case 'ASSUMED_APPROVED': return 'warning';
    case 'RECEIVED': return 'default';
    default: return 'secondary';
  }
}

function spaceTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    stue: 'Stue', kjøkken: 'Kjøkken', soverom: 'Soverom', bad: 'Baderom',
    bod: 'Bod', gang: 'Gang/Entre', wc: 'WC', kontor: 'Kontor',
    vaskerom: 'Vaskerom', balkong: 'Balkong', terrasse: 'Terrasse',
    hybel: 'Hybel', kjeller: 'Kjeller', loft: 'Loft', garasje: 'Garasje',
  };
  return labels[type.toLowerCase()] ?? type;
}

function groupByFloor(spaces: StructuredPlan['spaces']): Map<number, StructuredPlan['spaces']> {
  const map = new Map<number, StructuredPlan['spaces']>();
  for (const space of spaces) {
    const floor = space.floor_number ?? 1;
    if (!map.has(floor)) map.set(floor, []);
    map.get(floor)!.push(space);
  }
  return new Map([...map.entries()].sort(([a], [b]) => a - b));
}

export default function PlanPage() {
  const params = useParams();
  const caseId = params.id as string;

  const { data: plans, isLoading, error } = useSWR(
    `plans-${caseId}`,
    () => getPlans(caseId)
  );

  if (isLoading) {
    return (
      <div className="p-6 text-muted-foreground text-sm">Laster plandata…</div>
    );
  }

  if (error || !plans) {
    return (
      <div className="p-6 text-sm text-red-500">
        Kunne ikke hente plandata. Last opp og behandle et plandokument for å se data her.
      </div>
    );
  }

  if (plans.length === 0) {
    return (
      <div className="p-6">
        <h1 className="text-xl font-semibold mb-2">Strukturerte planer</h1>
        <p className="text-muted-foreground text-sm">
          Ingen plandata tilgjengelig ennå. Last opp et plandokument (plantegning) og vent på at det
          blir behandlet.
        </p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Strukturerte planer</h1>
        <p className="text-sm text-muted-foreground mt-1">
          {plans.length} plan{plans.length !== 1 ? 'er' : ''} tilgjengelig fra behandlede dokumenter
        </p>
      </div>

      <Tabs defaultValue={plans[0].id}>
        <TabsList className="flex-wrap h-auto gap-1">
          {plans.map((plan, i) => (
            <TabsTrigger key={plan.id} value={plan.id} className="text-xs">
              {plan.document_filename ?? `Plan ${i + 1}`}
            </TabsTrigger>
          ))}
        </TabsList>

        {plans.map((plan) => {
          const floorGroups = groupByFloor(plan.spaces);
          const totalArea = plan.total_area ?? plan.spaces.reduce((s, sp) => s + (sp.area ?? 0), 0);

          return (
            <TabsContent key={plan.id} value={plan.id} className="space-y-4 mt-4">
              {/* Plan summary card */}
              <Card>
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-4">
                    <CardTitle className="text-base">
                      {plan.document_filename ?? 'Plandokument'}
                    </CardTitle>
                    <Badge variant={approvalStatusVariant(plan.approval_status)}>
                      {approvalStatusLabel(plan.approval_status)}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground block text-xs">Totalt areal</span>
                      <span className="font-medium">{totalArea.toFixed(1)} m²</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground block text-xs">Antall rom</span>
                      <span className="font-medium">{plan.room_count ?? plan.spaces.length}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground block text-xs">Etasjer</span>
                      <span className="font-medium">{floorGroups.size}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground block text-xs">Dokumenttype</span>
                      <span className="font-medium">{plan.document_type ?? '—'}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Per-floor room tables */}
              {Array.from(floorGroups.entries()).map(([floorNum, spaces]) => (
                <Card key={floorNum}>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Etasje {floorNum}
                      <span className="ml-2 text-xs">
                        ({spaces.length} rom •{' '}
                        {spaces.reduce((s, sp) => s + (sp.area ?? 0), 0).toFixed(1)} m²)
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Rom</TableHead>
                          <TableHead>Type</TableHead>
                          <TableHead className="text-right">Areal (m²)</TableHead>
                          <TableHead className="text-right">Datakvalitet</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {spaces.map((space) => (
                          <TableRow key={space.id}>
                            <TableCell className="font-medium">{space.name}</TableCell>
                            <TableCell>{spaceTypeLabel(space.space_type)}</TableCell>
                            <TableCell className="text-right">
                              {space.area != null ? space.area.toFixed(1) : '—'}
                            </TableCell>
                            <TableCell className="text-right">
                              <ConfidenceIndicator confidence={space.confidence} showLabel={false} />
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              ))}
            </TabsContent>
          );
        })}
      </Tabs>
    </div>
  );
}
