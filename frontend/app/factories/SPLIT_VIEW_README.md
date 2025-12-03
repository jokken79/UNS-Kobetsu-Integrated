# Factories Split View Page

## Overview
The new integrated factories page (`/factories`) implements a complete Split View design pattern for efficient factory management. This page combines the FactoryTree, FactoryDetail, and LineCard components into a cohesive interface.

## Layout Structure

```
┌─────────────────────┬───────────────────────────────────────────────┐
│                     │                                               │
│   FactoryTree       │              FactoryDetail                    │
│   (280px fixed)     │              (flex-1)                         │
│                     │                                               │
│   - Search          │   - Factory info (editable)                   │
│   - Company groups  │   - Responsible persons                       │
│   - Factory list    │   - Lines with LineCard                       │
│   - New button      │   - Employees per line                        │
│                     │                                               │
└─────────────────────┴───────────────────────────────────────────────┘
```

## Key Features

### 1. Factory Tree (Left Panel)
- **Search**: Real-time filtering of factories
- **Grouped Display**: Factories grouped by company name
- **Auto-expand**: Selected factory's company automatically expands
- **Visual Indicators**: Active/inactive status shown with colored dots
- **Line Count**: Shows number of lines for each factory
- **New Factory**: Quick access button to create new factories

### 2. Factory Details (Right Panel)
- **Inline Editing**: Edit factory information without modal
- **Information Cards**:
  - Company Information
  - Factory/Plant Information
  - Responsible Person Details
  - Complaint Contact Details
- **Key Settings**: Conflict date and break minutes
- **Save/Cancel**: Confirmation flow for edits

### 3. Production Lines Section
- **LineCard Components**: Rich display of line information
- **Employee Assignment**: Shows employees assigned to each line
- **Hourly Rates**: Visual comparison of employee rates vs base rate
- **Expand/Collapse**: Individual control for each line card
- **Unassigned Employees**: Special section for employees without line assignment

## Data Flow

```typescript
// Main data queries
1. Factory List → FactoryTree
2. Selected Factory Details → FactoryDetail
3. Factory Employees → Grouped by line_id → LineCard

// Employee grouping logic
employeesByLine = Map<lineId, EmployeeResponse[]>
- null key = unassigned employees
- number key = assigned to specific line
```

## Component Communication

1. **Factory Selection**
   - User clicks factory in tree
   - `setSelectedFactoryId(factoryId)`
   - Triggers detail and employee queries
   - Auto-resets edit mode and expanded lines

2. **Factory Editing**
   - Edit button → `setIsEditingFactory(true)`
   - Form fields become editable
   - Save → API mutation → Toast notification
   - Cancel → Reset form data

3. **Line Management**
   - Expand/collapse individual lines
   - Edit line → Navigate to edit page
   - Delete line → Confirmation → API call
   - Add line → Navigate to create page

## API Endpoints Used

```typescript
// Factory queries
GET /api/v1/factories         // List all factories
GET /api/v1/factories/{id}    // Get factory details with lines
PUT /api/v1/factories/{id}    // Update factory
DELETE /api/v1/factories/{id} // Delete factory

// Employee queries
GET /api/v1/employees?factory_id={id} // Get factory employees

// Line operations
DELETE /api/v1/factories/lines/{id} // Delete line
```

## State Management

```typescript
// Component state
selectedFactoryId: number | null  // Currently selected factory
isEditingFactory: boolean         // Edit mode for factory details
factoryFormData: FactoryUpdate    // Form data during edit
expandedLines: Set<number>        // Expanded state for line cards

// React Query cache keys
['factories', 'list']              // All factories
['factories', factoryId]           // Single factory details
['employees', 'by-factory', id]   // Factory employees
```

## User Experience Features

1. **Auto-select First Factory**: Automatically selects the first factory on page load
2. **Loading Skeletons**: Shows skeleton loaders during data fetching
3. **Empty States**: Clear messaging when no data is available
4. **Toast Notifications**: Success/error feedback for actions
5. **Confirmation Dialogs**: Prevents accidental deletions
6. **Breadcrumbs**: Navigation context at the top

## Edge Cases Handled

1. **No Factories**: Shows empty state with factory icon
2. **No Lines**: Shows call-to-action to add first line
3. **Unassigned Employees**: Special section with yellow background
4. **Loading States**: Skeleton loaders for all async operations
5. **Error States**: Toast notifications for failures
6. **Type Casting**: Handles EmployeeListItem → EmployeeResponse conversion

## Responsive Design

- Fixed width tree (280px) for consistent navigation
- Scrollable content areas prevent layout overflow
- Grid layouts adapt to available space
- Collapsible sections optimize vertical space

## Future Enhancements

1. **Mobile View**: Toggle between tree and detail on small screens
2. **Bulk Operations**: Select multiple lines for batch actions
3. **Drag & Drop**: Reassign employees between lines
4. **Real-time Updates**: WebSocket for live employee updates
5. **Export**: Download factory/line/employee data

## Usage Example

```typescript
// Navigate to the page
router.push('/factories')

// The page will:
1. Load all factories into the tree
2. Auto-select the first factory
3. Load factory details and employees
4. Group employees by their assigned lines
5. Display everything in the split view
```

## Testing Considerations

1. Test with large factory lists (100+ factories)
2. Test with many employees per line (50+ employees)
3. Test edit/save/cancel flows
4. Test delete confirmations
5. Test search filtering performance
6. Test line expansion state persistence