# ConfirmDialog Usage Guide

## Setup

The ConfirmDialog system is already integrated into the application through the providers. No additional setup is required.

## Basic Usage

### Import the hook in your component:

```tsx
import { useConfirm } from '@/components/common/ConfirmContext'
```

### Simple confirmation:

```tsx
const { confirm } = useConfirm()

const handleDelete = async () => {
  const confirmed = await confirm({
    type: 'danger',
    title: '削除の確認',
    message: 'このアイテムを削除しますか？この操作は取り消せません。',
    confirmText: '削除する',
    cancelText: 'キャンセル'
  })

  if (confirmed) {
    // Proceed with delete operation
    await deleteItem()
  }
}
```

## Using Convenience Hooks

For common scenarios, use the pre-configured actions:

```tsx
import { useConfirmActions } from '@/components/common/ConfirmContext'

export function MyComponent() {
  const { confirmDelete, confirmWarning, confirmInfo } = useConfirmActions()

  // Delete confirmation with item name
  const handleDeleteFactory = async () => {
    const confirmed = await confirmDelete('高雄工業')
    if (confirmed) {
      await deleteFactory()
    }
  }

  // Warning confirmation
  const handleRiskyOperation = async () => {
    const confirmed = await confirmWarning(
      '注意が必要です',
      'この操作は複数のレコードに影響します。続行しますか？'
    )
    if (confirmed) {
      await performRiskyOperation()
    }
  }
}
```

## Real-World Examples

### Factory Delete Button

```tsx
// In components/factory/FactoryTable.tsx
import { useConfirmActions } from '@/components/common/ConfirmContext'
import { useToastActions } from '@/components/common/ToastContext'
import { useDeleteFactory } from '@/hooks/useFactory'

export function FactoryTable({ factories }) {
  const { confirmDelete } = useConfirmActions()
  const toast = useToastActions()
  const deleteMutation = useDeleteFactory()

  const handleDelete = async (factory) => {
    const confirmed = await confirmDelete(factory.factory_name)

    if (confirmed) {
      try {
        await deleteMutation.mutateAsync(factory.id)
        toast.success('工場を削除しました')
      } catch (error) {
        toast.error('削除に失敗しました')
      }
    }
  }

  return (
    // ... table JSX
    <button onClick={() => handleDelete(factory)}>
      削除
    </button>
  )
}
```

### Kobetsu Contract Form with Unsaved Changes

```tsx
// In components/kobetsu/KobetsuForm.tsx
import { useRouter } from 'next/navigation'
import { useConfirmActions } from '@/components/common/ConfirmContext'
import { useState, useEffect } from 'react'

export function KobetsuForm() {
  const router = useRouter()
  const { confirmSave } = useConfirmActions()
  const [hasChanges, setHasChanges] = useState(false)

  // Intercept navigation when there are unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (hasChanges) {
        e.preventDefault()
        e.returnValue = ''
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [hasChanges])

  const handleCancel = async () => {
    if (hasChanges) {
      const confirmed = await confirmSave(true)
      if (!confirmed) {
        return // Stay on page
      }
    }
    router.push('/kobetsu')
  }

  return (
    // ... form JSX
    <button onClick={handleCancel}>
      キャンセル
    </button>
  )
}
```

### Employee Assignment with Warning

```tsx
// In components/kobetsu/EmployeeAssignment.tsx
import { useConfirmActions } from '@/components/common/ConfirmContext'

export function EmployeeAssignment({ kobetsu, employees }) {
  const { confirmWarning } = useConfirmActions()

  const handleAssignEmployee = async (employee) => {
    // Check for conflicts
    if (employee.current_assignment) {
      const confirmed = await confirmWarning(
        '既存の割り当て',
        `${employee.full_name}は既に別の契約に割り当てられています。上書きしますか？`
      )

      if (!confirmed) {
        return
      }
    }

    // Proceed with assignment
    await assignEmployee(kobetsu.id, employee.id)
  }

  return (
    // ... component JSX
  )
}
```

## Keyboard Shortcuts

The ConfirmDialog supports keyboard navigation:

- **Enter**: Focus moves to confirm button when dialog opens
- **Ctrl+Enter**: Confirm the action
- **Escape**: Cancel the dialog
- **Tab**: Navigate between buttons

## Dialog Types

### `danger` (Red - Destructive actions)
- Delete operations
- Permanent removals
- Data loss scenarios

### `warning` (Amber - Caution needed)
- Overwrite operations
- Conflicting data
- Potentially risky actions

### `info` (Blue - Information)
- Confirmations
- Process starts
- Neutral decisions

## Accessibility Features

- Focus management (auto-focus confirm button)
- Keyboard navigation support
- Screen reader friendly with proper ARIA attributes
- Focus trap within dialog
- Body scroll lock when dialog is open

## Testing

To test the ConfirmDialog in development:

1. Import the demo component:
```tsx
import { ConfirmDialogDemo } from '@/components/common/ConfirmDialogDemo'
```

2. Add it to a page:
```tsx
export default function TestPage() {
  return <ConfirmDialogDemo />
}
```

3. Test various scenarios using the demo buttons

## Best Practices

1. **Use appropriate types**: Choose `danger` for deletions, `warning` for risky operations, `info` for neutral confirmations
2. **Clear messaging**: Make the consequences clear in the message
3. **Actionable button text**: Use verbs that clearly indicate the action (削除する, 保存する, 続行する)
4. **Handle both outcomes**: Always handle both confirmed and cancelled cases
5. **Combine with toast**: Show success/failure feedback after the action completes