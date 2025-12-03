# Toast Notification System

A modern, animated toast notification system for the UNS-Kobetsu-Integrated frontend.

## Features

- 🎨 **4 Toast Types**: success, error, warning, info
- ⏱️ **Auto-dismiss**: Configurable duration with visual progress bar
- 🎯 **Manual dismiss**: Close button for immediate dismissal
- 📚 **Stack Management**: Maximum 5 toasts displayed simultaneously
- ✨ **Smooth Animations**: Slide-in/out with fade effects
- 🎭 **Icons**: Distinct icons for each toast type

## Installation

The Toast system is already integrated into the application. Dependencies:
- `@heroicons/react`: Icon components
- React 18+
- Tailwind CSS

## Basic Usage

```tsx
import { useToast } from '@/components/common/Toast'

function MyComponent() {
  const { showToast } = useToast()

  const handleAction = () => {
    showToast({
      type: 'success',
      message: '操作が成功しました'
    })
  }

  return <button onClick={handleAction}>Show Toast</button>
}
```

## Convenience Methods

Use the `useToastActions` hook for typed convenience methods:

```tsx
import { useToastActions } from '@/components/common/Toast'

function MyComponent() {
  const toast = useToastActions()

  return (
    <>
      <button onClick={() => toast.success('成功!')}>Success</button>
      <button onClick={() => toast.error('エラー!')}>Error</button>
      <button onClick={() => toast.warning('警告!')}>Warning</button>
      <button onClick={() => toast.info('情報')}>Info</button>
    </>
  )
}
```

## Advanced Usage

### Custom Duration

```tsx
// Display for 10 seconds
showToast({
  type: 'error',
  message: '重要なエラーメッセージ',
  duration: 10000 // milliseconds
})

// Never auto-dismiss (manual close only)
showToast({
  type: 'info',
  message: '手動で閉じてください',
  duration: 0
})
```

### Real-world Examples

```tsx
// API Success
try {
  const result = await api.post('/kobetsu', data)
  toast.success('契約書が作成されました')
  router.push(`/kobetsu/${result.id}`)
} catch (error) {
  toast.error('契約書の作成に失敗しました')
}

// Form Validation
if (!formData.factory_id) {
  toast.warning('派遣先を選択してください')
  return
}

// Background Sync
toast.info('データを同期中...')
await syncData()
toast.success('同期が完了しました')
```

## Styling

The Toast system uses Tailwind CSS with these color schemes:

| Type | Background | Icon | Border |
|------|------------|------|---------|
| Success | emerald-500 | CheckCircleIcon | emerald-200 |
| Error | red-500 | XCircleIcon | red-200 |
| Warning | amber-500 | ExclamationTriangleIcon | amber-200 |
| Info | blue-500 | InformationCircleIcon | blue-200 |

## Component Structure

```
Toast/
├── Toast.tsx          # Individual toast component
├── ToastContainer.tsx # Container for positioning and stacking
├── ToastContext.tsx   # Context provider and hooks
├── index.ts          # Export barrel
└── README.md         # This file
```

## Demo

Visit `/demo/toast` to see a live demo with various examples.

## API Reference

### `showToast(options)`

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| type | `'success' \| 'error' \| 'warning' \| 'info'` | required | Toast type |
| message | `string` | required | Message to display |
| duration | `number` | 5000 | Auto-dismiss duration in ms (0 = no auto-dismiss) |

### `useToast()`

Returns:
- `showToast(options)`: Function to display a toast
- `clearToasts()`: Function to clear all toasts

### `useToastActions()`

Returns convenience methods:
- `success(message, duration?)`: Show success toast
- `error(message, duration?)`: Show error toast
- `warning(message, duration?)`: Show warning toast
- `info(message, duration?)`: Show info toast

## Limitations

- Maximum 5 toasts displayed simultaneously (older ones are removed)
- Toast position is fixed to bottom-right on desktop, bottom on mobile
- No support for custom actions/buttons within toasts (by design)

## Testing

The Toast system can be tested by:
1. Running the application: `npm run dev`
2. Navigating to `/demo/toast`
3. Testing various scenarios using the demo buttons

## Future Enhancements

Potential improvements:
- [ ] Position configuration (top, bottom, left, right)
- [ ] Toast with actions (Undo, Retry, etc.)
- [ ] Persistence across page navigation
- [ ] Sound notifications
- [ ] Accessibility improvements (screen reader announcements)