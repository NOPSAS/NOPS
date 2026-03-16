'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  Building2,
  LayoutDashboard,
  FolderOpen,
  LogOut,
  User,
  ChevronDown,
  MapPin,
  CreditCard,
  Wrench,
  Sparkles,
  BarChart3,
  Menu,
  X,
  TrendingUp,
  Newspaper,
  Package,
  Trees,
  Search,
  FileText,
  Scale,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { logout } from '@/lib/api';
import { useAuth } from '@/app/auth-provider';

interface NavLinkProps {
  href: string;
  children: React.ReactNode;
  icon?: React.ReactNode;
  onClick?: () => void;
}

function NavLink({ href, children, icon, onClick }: NavLinkProps) {
  const pathname = usePathname();
  const isActive =
    href === '/' ? pathname === '/' : pathname.startsWith(href);

  return (
    <Link
      href={href}
      onClick={onClick}
      className={cn(
        'inline-flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors',
        isActive
          ? 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-slate-100'
          : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50 dark:text-slate-400 dark:hover:text-slate-100 dark:hover:bg-slate-800'
      )}
      aria-current={isActive ? 'page' : undefined}
    >
      {icon}
      {children}
    </Link>
  );
}

const AUTH_NAV = [
  { href: '/', label: 'Dashboard', icon: <LayoutDashboard className="h-4 w-4" /> },
  { href: '/cases', label: 'Saker', icon: <FolderOpen className="h-4 w-4" /> },
  { href: '/property', label: 'Eiendom', icon: <MapPin className="h-4 w-4" /> },
  { href: '/tjenester', label: 'Tjenester', icon: <Wrench className="h-4 w-4" /> },
  { href: '/visualisering', label: 'Visualisering', icon: <Sparkles className="h-4 w-4" /> },
  { href: '/pakke', label: 'Pakke', icon: <Package className="h-4 w-4" /> },
  { href: '/utbygging', label: 'Utbygging', icon: <BarChart3 className="h-4 w-4" /> },
  { href: '/tomter', label: 'Tomter', icon: <Trees className="h-4 w-4" /> },
  { href: '/investering', label: 'Investering', icon: <TrendingUp className="h-4 w-4" /> },
  { href: '/dispensasjon', label: 'Dispensasjon', icon: <Scale className="h-4 w-4" /> },
  { href: '/nyheter', label: 'Nyheter', icon: <Newspaper className="h-4 w-4" /> },
  { href: '/finn-analyse', label: 'Finn-analyse', icon: <Search className="h-4 w-4" /> },
  { href: '/dokumenter', label: 'Dokumenter', icon: <FileText className="h-4 w-4" /> },
];

const GUEST_NAV = [
  { href: '/landing', label: 'Om tjenesten' },
  { href: '/nyheter', label: 'Nyheter' },
  { href: '/tjenester', label: 'Tjenester' },
  { href: '/pricing', label: 'Priser' },
];

// Desktop: vis maks 5 lenker, resten i "Mer"-dropdown
const DESKTOP_MAX = 5;

export function Navbar() {
  const router = useRouter();
  const { user } = useAuth();
  const [menuOpen, setMenuOpen] = React.useState(false);
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const menuRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Lukk mobil-meny ved navigasjon
  const closeMobile = () => setMobileOpen(false);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const navItems = user ? AUTH_NAV : GUEST_NAV;
  const desktopVisible = navItems.slice(0, DESKTOP_MAX);
  const desktopOverflow = navItems.slice(DESKTOP_MAX);

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        {/* Brand */}
        <Link
          href="/"
          className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white hover:opacity-80 transition-opacity"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
            <Building2 className="h-5 w-5 text-white" aria-hidden="true" />
          </div>
          <span className="text-lg">ByggSjekk</span>
        </Link>

        {/* Desktop nav */}
        <nav
          className="hidden md:flex items-center gap-1"
          aria-label="Hovednavigasjon"
        >
          {desktopVisible.map((item) => (
            <NavLink key={item.href} href={item.href} icon={'icon' in item ? item.icon : undefined}>
              {item.label}
            </NavLink>
          ))}

          {/* Overflow "Mer"-dropdown */}
          {desktopOverflow.length > 0 && (
            <div className="relative">
              <button
                type="button"
                onClick={() => setMenuOpen((v) => (v ? false : true))}
                className="inline-flex items-center gap-1 px-3 py-2 rounded-md text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors"
              >
                Mer
                <ChevronDown className="h-3.5 w-3.5" />
              </button>
              {menuOpen && (
                <div className="absolute right-0 mt-1 w-48 rounded-lg border border-slate-200 bg-white py-1 shadow-lg z-50">
                  {desktopOverflow.map((item) => (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setMenuOpen(false)}
                      className="flex items-center gap-2 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
                    >
                      {'icon' in item && item.icon}
                      {item.label}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )}
        </nav>

        <div className="flex items-center gap-2">
          {/* Hamburger (mobil) */}
          <button
            type="button"
            onClick={() => setMobileOpen((v) => !v)}
            className="md:hidden inline-flex items-center justify-center rounded-lg p-2 text-slate-600 hover:bg-slate-100 transition-colors"
            aria-label="Meny"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>

          {/* User menu */}
          <div className="relative" ref={menuRef}>
            <button
              type="button"
              onClick={() => setMenuOpen((v) => !v)}
              className="hidden md:inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 transition-colors dark:text-slate-300 dark:hover:bg-slate-800"
              aria-expanded={menuOpen}
              aria-haspopup="menu"
            >
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900">
                <User className="h-4 w-4 text-blue-700 dark:text-blue-300" aria-hidden="true" />
              </div>
              <span className="hidden sm:block max-w-[160px] truncate">
                {user?.full_name ?? 'Konto'}
              </span>
              <ChevronDown
                className={cn(
                  'h-4 w-4 text-slate-400 transition-transform duration-200',
                  menuOpen && 'rotate-180'
                )}
                aria-hidden="true"
              />
            </button>

            {menuOpen && (
              <div
                role="menu"
                className="absolute right-0 mt-2 w-56 rounded-lg border border-slate-200 bg-white py-1 shadow-lg dark:border-slate-700 dark:bg-slate-900 z-50"
              >
                {user && (
                  <div className="px-4 py-2 border-b border-slate-100 dark:border-slate-700">
                    <p className="text-xs text-muted-foreground">Innlogget som</p>
                    <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                      {user.email}
                    </p>
                  </div>
                )}
                {user && (
                  <Link
                    href="/account/billing"
                    role="menuitem"
                    onClick={() => setMenuOpen(false)}
                    className="flex w-full items-center gap-2 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800 transition-colors"
                  >
                    <CreditCard className="h-4 w-4" aria-hidden="true" />
                    Abonnement
                  </Link>
                )}
                {!user && (
                  <>
                    <Link
                      href="/login"
                      role="menuitem"
                      onClick={() => setMenuOpen(false)}
                      className="flex w-full items-center gap-2 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
                    >
                      <User className="h-4 w-4" />
                      Logg inn
                    </Link>
                    <Link
                      href="/register"
                      role="menuitem"
                      onClick={() => setMenuOpen(false)}
                      className="flex w-full items-center gap-2 px-4 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 transition-colors"
                    >
                      Opprett konto
                    </Link>
                  </>
                )}
                {user && (
                  <button
                    type="button"
                    role="menuitem"
                    onClick={handleLogout}
                    className="flex w-full items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-950 transition-colors"
                  >
                    <LogOut className="h-4 w-4" aria-hidden="true" />
                    Logg ut
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Mobil-meny */}
      {mobileOpen && (
        <div className="md:hidden border-t border-slate-200 bg-white dark:bg-slate-900">
          <nav className="container mx-auto px-4 py-3 flex flex-col gap-1">
            {navItems.map((item) => (
              <NavLink key={item.href} href={item.href} icon={'icon' in item ? item.icon : undefined} onClick={closeMobile}>
                {item.label}
              </NavLink>
            ))}
            <div className="border-t border-slate-200 my-2" />
            {user ? (
              <>
                <NavLink href="/account/billing" icon={<CreditCard className="h-4 w-4" />} onClick={closeMobile}>
                  Abonnement
                </NavLink>
                <button
                  type="button"
                  onClick={() => { closeMobile(); handleLogout(); }}
                  className="inline-flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
                >
                  <LogOut className="h-4 w-4" />
                  Logg ut
                </button>
              </>
            ) : (
              <>
                <NavLink href="/login" onClick={closeMobile}>Logg inn</NavLink>
                <Link
                  href="/register"
                  onClick={closeMobile}
                  className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 transition-colors mt-1"
                >
                  Opprett gratis konto
                </Link>
              </>
            )}
          </nav>
        </div>
      )}
    </header>
  );
}
