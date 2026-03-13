# FX Trading Tracker - Product Requirements Document

## Original Problem Statement
Mobile-responsive full-stack FX Trading Tracker platform with:
- Secure login with role-based access (Admin, Trader, Treasury Operations)
- Trader: Log Deal Tickets, cancel submitted deals, resubmit returned deals
- Treasury: View/process Deal Tickets (confirm/return), upload settlement proofs, mandatory remarks
- Admin: Manage reference data, manage users, view audit trail
- All roles: Export deal data to CSV
- Crypto + Fiat currency support, Bank/Crypto toggles, "Ours" section
- Server-side pagination, lazy loading, performant UI

## Architecture
- **Backend:** FastAPI + MongoDB (motor) + JWT auth
- **Frontend:** React + TailwindCSS + Shadcn UI
- **Storage:** Emergent Object Storage for settlement proofs
- **DB Collections:** users, deals, audit_logs

## Credentials
- Trader: trader@fxtracker.com / Trader@123
- Treasury: treasury@fxtracker.com / Treasury@123
- Admin: admin@fxtracker.com / Admin@123

## What's Been Implemented
- [x] Role-based authentication (Admin, Trader, Treasury)
- [x] Complete deal lifecycle: create, review, confirm, return, cancel, resubmit
- [x] Server-side pagination on all tables
- [x] Debounced filter inputs
- [x] CSV export for deals
- [x] Audit trail page (Admin)
- [x] User management (Admin)
- [x] Settlement proof upload (Treasury)
- [x] Bank/Crypto toggle and "Ours" section on deal form
- [x] **P0 Performance Fix (Feb 2026):** React.memo on all table rows (DealRow, TreasuryRow, TxRow, UserRow, AuditRow) + useCallback for handlers. Modal open times reduced from ~12s to <0.2s
- [x] **Dialog Close Overlay Fix (Mar 2026):** Reduced overlay from bg-black/80 to bg-black/40, sped up animation to 150ms, and implemented useRef pattern to preserve dialog content during exit animation. Eliminates black flash on modal close.
- [x] **Comprehensive Performance Overhaul (Mar 2026):**
  - Auth: Reads localStorage immediately, no longer blocks app rendering
  - Code splitting: React.lazy for all page components (reduces initial bundle)
  - Dashboard: Skeleton UI on first load, opacity fade on range change (keeps data visible)
  - All tables: Keep previous data visible during loading (opacity fade instead of blocking spinner)
  - Backend: Dashboard uses MongoDB $facet aggregation (no longer loads all docs into memory)
  - Layout: SidebarContent extracted as memo'd component
  - Dashboard table: RecentDealRow memo'd
  - Eliminated MutationObserver on document.body (was firing on every DOM mutation from dialog/toast portals). Replaced with CSS-only badge hiding.
- [x] **NewDealPage Performance Rewrite (Mar 2026):**
  - Moved TypeToggle outside component (was causing unmount/remount 3x per keystroke)
  - All sub-components memo'd: TypeToggle, SearchSelect, CurrSel, DatePick, CurrItem
  - Stable callbacks: up() with useCallback + functional updaters, single onInput using e.target.name
  - useMemo for derived currency arrays (fiat, stablecoin, crypto)
  - Name-based onChange pattern: onChange(name, value) for all memo'd components
- [x] **ReferenceDataPage Optimization (Mar 2026):** RefRow memo, useCallback for openEdit/del, smooth loading pattern
- [x] **StrictMode & CSS Performance Fix (Mar 2026):**
  - Removed React.StrictMode (was doubling all renders, effects, and API calls)
  - Replaced `transition-all` with `transition-colors` on interactive elements (prevents layout thrashing)
  - Fixed tabs.jsx, Layout.jsx nav links, TypeToggle buttons
- [x] **Loading Flash Fix (Mar 2026):** Applied hasLoaded ref pattern across all 6 data pages — loading spinner only shows on initial load, subsequent fetches (filter/pagination/tab) update silently. Debounce reduced from 400ms to 250ms.
- [x] **Proof of Payment Upload at Deal Creation (Mar 2026):** Trader can select and upload settlement proof files during deal creation. Files uploaded after deal is created via POST /deals/{id}/upload.
- [x] **Global RefData Cache (Mar 2026):** Created RefDataContext to fetch reference data once on login and cache globally. NewDealPage loads instantly (106ms on repeat visit) with pre-populated dropdowns — eliminated 5 API calls per visit. ReferenceDataPage mutations invalidate the cache via reload().
- [x] **Instant Deal Dialog (Mar 2026):** Eliminated redundant API call when viewing deal detail on My Deals page — dialog now opens in 78ms using data already in table row.
- [x] **Dashboard Stats Caching (Mar 2026):** Module-level cache (`statsCache`, `cachedRange`) persists across unmount/remount. Return navigation to Dashboard renders in ~128ms with zero skeleton/loading states. Cache invalidates automatically on date range change. Verified for all 3 roles.
- [x] **Dashboard Chart Performance (Mar 2026):** Disabled recharts default animations (`isAnimationActive={false}`) on Bar and Pie charts — eliminates 1.5s SVG animation jank. Extracted DealsChart/StatusChart as memo'd components. Memoized pieData with useMemo and Metric with React.memo.
- [x] **Idle Page Prefetching (Mar 2026):** All React.lazy page chunks are prefetched via `requestIdleCallback` after login. Eliminates Suspense spinner on first navigation to any page. New Deal page loads in ~108ms on repeat visits.
- [x] **Browser Hang / CPU Drain Fix (Mar 2026):** Root cause: MutationObserver on document.body in index.html watching every DOM change (childList, subtree, attributes) — fired on every React render. Removed. Also: eliminated duplicate Google Fonts CSS @import (was loaded twice), switched to non-blocking font load (media=print onload), reduced font weights (10→5), removed 28 debug-wrapper CSS inherit rules, staggered idle prefetch (150ms between chunks vs all-at-once), optimized login image (q=60, w=800, decoding=async).

## P0/P1/P2 Backlog
- No pending issues or feature requests. All performance optimizations complete.

## Key Files
- `backend/server.py` - All API endpoints
- `frontend/src/pages/DealsPage.jsx` - Trader deals view (DealRow memo)
- `frontend/src/pages/TreasuryPage.jsx` - Treasury review (TreasuryRow memo)
- `frontend/src/pages/TransactionHistoryPage.jsx` - Admin transaction history (TxRow memo)
- `frontend/src/pages/UsersPage.jsx` - Admin user management (UserRow memo)
- `frontend/src/pages/AuditLogPage.jsx` - Admin audit trail (AuditRow memo)
