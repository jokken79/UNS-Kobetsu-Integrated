# Rate Group Preview Integration - Implementation Summary

## Overview
Successfully integrated the RateGroupPreview component into the contract creation workflow in UNS-Kobetsu-Integrated. The system now checks if selected employees have different hourly rates and offers options to either split them into multiple contracts or create a single contract.

## Files Modified

### 1. `/frontend/lib/api.ts`
Added two new API functions to the kobetsuApi object:

```typescript
// Group employees by their hourly rate
groupByRate: async (employeeIds: number[]) => {
  const response = await apiClient.post('/kobetsu/group-by-rate', { employee_ids: employeeIds })
  return response.data
}

// Create multiple contracts in batch
batchCreate: async (data: {
  factory_id: number
  base_contract_data: Partial<KobetsuCreate>
  groups: Array<{
    employee_ids: number[]
    hourly_rate: number
    billing_rate?: number
  }>
}) => {
  const response = await apiClient.post('/kobetsu/batch-create', data)
  return response.data
}
```

### 2. `/frontend/app/kobetsu/create/page.tsx`
Enhanced the create page with rate checking logic:

#### New State Variables:
- `showRatePreview`: Controls visibility of the RateGroupPreview modal
- `rateGroups`: Stores the grouped employee data from API
- `isCheckingRates`: Loading state while checking rates
- `pendingFormData`: Stores form data while showing preview

#### Enhanced Submit Flow:
1. **Single Employee**: Creates contract directly
2. **Multiple Employees**:
   - Calls `/kobetsu/group-by-rate` API to check rates
   - If rates differ: Shows RateGroupPreview modal
   - If rates same: Creates single contract

#### New Handler Functions:
- `handleRatePreviewConfirm(splitByRate)`: Handles user choice from preview
  - If split: Calls batch create API with grouped data
  - If single: Creates one contract with uniform rate
- `handleRatePreviewCancel()`: Cancels the preview and clears state

#### UI Updates:
- Added RateGroupPreview modal component to render when needed
- Updated loading states to include rate checking
- Added toast notifications for success/error messages

### 3. `/frontend/components/kobetsu/KobetsuFormHybrid.tsx`
Minor update to button text:
- Changed "作成中..." to "処理中..." to be more generic

## User Flow

1. **User fills out contract form** with multiple employees
2. **Clicks "契約書を作成"** button
3. **System checks employee rates** via API
4. **If rates differ:**
   - Shows RateGroupPreview modal
   - Displays grouped employees by rate
   - User chooses:
     - "Split by rate" (recommended) → Creates multiple contracts
     - "Single contract" → Creates one contract with uniform rate
5. **If rates same:** Creates single contract immediately
6. **Success:**
   - Shows success toast with contract count
   - Redirects to contract list (batch) or detail page (single)

## Key Features

### Smart Rate Detection
- Automatically detects when employees have different hourly rates
- Groups employees by their individual rates from Base Madre
- Shows visual preview of how contracts will be split

### Flexible Options
- Users can override the recommendation
- Single contract option maintains form's hourly rate for all
- Batch creation preserves individual rates per group

### Error Handling
- Fallback to single contract if rate check fails
- Toast notifications for all outcomes
- Proper loading states during async operations

## API Endpoints Required (Backend)

The frontend expects these endpoints to exist:

1. **POST /api/v1/kobetsu/group-by-rate**
   - Input: `{ employee_ids: number[] }`
   - Output: Rate group data with employees

2. **POST /api/v1/kobetsu/batch-create**
   - Input: Batch creation data with groups
   - Output: Success status and created contract IDs

## Testing Checklist

- [ ] Single employee creation works without rate check
- [ ] Multiple employees with same rate creates single contract
- [ ] Multiple employees with different rates shows preview
- [ ] "Split by rate" creates correct number of contracts
- [ ] "Single contract" creates one contract with form rate
- [ ] Cancel button closes preview without action
- [ ] Loading states display correctly
- [ ] Toast messages appear for success/errors
- [ ] Navigation works after creation

## Benefits

1. **Compliance**: Ensures proper rate documentation per Japanese labor law
2. **Efficiency**: Batch creation saves time vs manual splitting
3. **Flexibility**: Users maintain control over contract structure
4. **Transparency**: Visual preview shows exactly what will be created
5. **Data Integrity**: Preserves individual employee rates from Base Madre