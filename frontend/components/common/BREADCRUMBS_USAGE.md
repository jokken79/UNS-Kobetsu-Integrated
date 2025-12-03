# Breadcrumbs Component Usage Guide

## Overview
The Breadcrumbs component provides a navigation trail showing the user's current location in the application hierarchy.

## Component Location
`/frontend/components/common/Breadcrumbs.tsx`

## Design Features
- **Home Icon**: First item displays with a home icon
- **Chevron Separators**: Between each breadcrumb item
- **Current Page**: Last item is not clickable (no href)
- **Clickable Links**: All other items are clickable navigation links
- **Text Styling**:
  - Links: `text-gray-500` with hover state `text-gray-700`
  - Current page: `text-gray-900`
  - Small text size: `text-sm`
- **Responsive**: Horizontal flex layout

## API

### BreadcrumbItem Interface
```typescript
interface BreadcrumbItem {
  label: string
  href?: string  // if undefined, it's the current page (not clickable)
}
```

### BreadcrumbsProps Interface
```typescript
interface BreadcrumbsProps {
  items: BreadcrumbItem[]
  className?: string
}
```

### Helper Export
```typescript
export const dashboardBreadcrumb: BreadcrumbItem = {
  label: 'ダッシュボード',
  href: '/'
}
```

## Usage Examples

### Basic Usage
```tsx
import { Breadcrumbs, dashboardBreadcrumb } from '@/components/common/Breadcrumbs'

<Breadcrumbs
  items={[
    dashboardBreadcrumb,
    { label: '派遣先企業', href: '/factories' },
    { label: '高雄工業株式会社' }  // current page, no href
  ]}
/>
```

### With Custom Styling
```tsx
<Breadcrumbs
  items={[...]}
  className="mb-6"
/>
```

## Current Implementations

The Breadcrumbs component has been integrated into the following pages:

1. **Factory Detail Page** (`/factories/[id]/page.tsx`)
   - Shows: ダッシュボード > 派遣先企業 > [Factory Name]

2. **Factory Create Page** (`/factories/create/page.tsx`)
   - Shows: ダッシュボード > 派遣先企業 > 新規作成

3. **Employee Detail Page** (`/employees/[id]/page.tsx`)
   - Shows: ダッシュボード > 従業員管理 > [Employee Name]

4. **Kobetsu Contract Detail Page** (`/kobetsu/[id]/page.tsx`)
   - Shows: ダッシュボード > 個別契約書 > [Contract Number]

5. **Kobetsu Contract Create Page** (`/kobetsu/create/page.tsx`)
   - Shows: ダッシュボード > 個別契約書 > 新規作成

## Accessibility Features

- Uses semantic `<nav>` element with `aria-label="Breadcrumb"`
- Current page marked with `aria-current="page"`
- Icons marked with `aria-hidden="true"` to avoid screen reader redundancy

## Dependencies

- `next/link` - For navigation links
- `@heroicons/react/24/outline` - For HomeIcon and ChevronRightIcon

## Future Enhancements

To add breadcrumbs to additional pages:

1. Import the component and helper:
   ```tsx
   import { Breadcrumbs, dashboardBreadcrumb } from '@/components/common/Breadcrumbs'
   ```

2. Add the component before the page header:
   ```tsx
   <Breadcrumbs
     items={[
       dashboardBreadcrumb,
       { label: 'Section Name', href: '/section' },
       { label: 'Current Page' }
     ]}
     className="mb-6"
   />
   ```

3. Ensure the last item has no `href` to indicate it's the current page