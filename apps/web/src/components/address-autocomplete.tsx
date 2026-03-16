'use client';

/**
 * AddressAutocomplete – adressesøk med autocomplete fra Geonorge.
 *
 * Bruk:
 *   <AddressAutocomplete
 *     onSelect={(suggestion) => { ... }}
 *     placeholder="Søk adresse..."
 *   />
 */

import * as React from 'react';
import { Search, MapPin, Loader2 } from 'lucide-react';
import { getAddressSuggestions } from '@/lib/api';
import type { AddressSuggestion } from '@/lib/api';
import { cn } from '@/lib/utils';

interface AddressAutocompleteProps {
  onSelect: (suggestion: AddressSuggestion) => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
  initialValue?: string;
}

export function AddressAutocomplete({
  onSelect,
  placeholder = 'Søk adresse...',
  className,
  disabled = false,
  initialValue = '',
}: AddressAutocompleteProps) {
  const [query, setQuery] = React.useState(initialValue);
  const [suggestions, setSuggestions] = React.useState<AddressSuggestion[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [open, setOpen] = React.useState(false);
  const [activeIndex, setActiveIndex] = React.useState(-1);
  const debounceRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);
  const containerRef = React.useRef<HTMLDivElement>(null);

  // Debounced search
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    setActiveIndex(-1);

    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (value.length < 3) {
      setSuggestions([]);
      setOpen(false);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const results = await getAddressSuggestions(value);
        setSuggestions(results);
        setOpen(results.length > 0);
      } catch {
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    }, 300);
  };

  const handleSelect = (suggestion: AddressSuggestion) => {
    setQuery(suggestion.adressetekst);
    setSuggestions([]);
    setOpen(false);
    onSelect(suggestion);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!open) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, suggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, -1));
    } else if (e.key === 'Enter' && activeIndex >= 0) {
      e.preventDefault();
      handleSelect(suggestions[activeIndex]);
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  };

  // Close on outside click
  React.useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div ref={containerRef} className={cn('relative', className)}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        {loading && (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-muted-foreground" />
        )}
        <input
          type="text"
          value={query}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onFocus={() => suggestions.length > 0 && setOpen(true)}
          placeholder={placeholder}
          disabled={disabled}
          autoComplete="off"
          className={cn(
            'w-full rounded-md border border-input bg-background pl-9 pr-9 py-2 text-sm',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
            'disabled:opacity-50',
          )}
          aria-autocomplete="list"
          aria-expanded={open}
        />
      </div>

      {open && suggestions.length > 0 && (
        <div className="absolute z-50 mt-1 w-full rounded-md border border-slate-200 bg-white shadow-lg dark:border-slate-700 dark:bg-slate-900">
          <ul role="listbox" className="max-h-64 overflow-y-auto py-1">
            {suggestions.map((s, i) => (
              <li
                key={`${s.kommunenummer}-${s.gnr}-${s.bnr}-${i}`}
                role="option"
                aria-selected={i === activeIndex}
                className={cn(
                  'flex cursor-pointer items-start gap-2 px-3 py-2.5 text-sm transition-colors',
                  i === activeIndex
                    ? 'bg-blue-50 text-blue-900 dark:bg-blue-950 dark:text-blue-100'
                    : 'hover:bg-slate-50 dark:hover:bg-slate-800',
                )}
                onClick={() => handleSelect(s)}
                onMouseEnter={() => setActiveIndex(i)}
              >
                <MapPin className="h-3.5 w-3.5 mt-0.5 shrink-0 text-muted-foreground" />
                <div className="min-w-0">
                  <p className="font-medium truncate">{s.adressetekst}</p>
                  <p className="text-xs text-muted-foreground">
                    {s.postnummer} {s.poststed}
                    {s.gnr && s.bnr && ` · Gnr/Bnr: ${s.gnr}/${s.bnr}`}
                    {s.kommunenavn && ` · ${s.kommunenavn}`}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
