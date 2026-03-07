# Campus Assist Theme Guide

## Theme Colors

### Primary Colors
- **Primary**: `#3a7bd5` - Main brand color (Calm Trust Blue)
- **Primary Light**: `#7aa7e6` - Light blue for hover states
- **Primary Hover**: `#2f65b4` - Darker shade for interaction
- **Primary Active**: `#244f8f` - Strongest shade for active states

### Secondary Colors
- **Secondary**: `#6bcb77` - Community Green
- **Secondary Hover**: `#54b864` - Darker green for interaction

### Accent Color
- **Accent**: `#ffb84c` - Friendly Orange
- **Accent Hover**: `#f5a623` - Darker orange for interaction

### Semantic Colors
- **Success**: `#4caf50` - Success/positive states
- **Warning**: `#f59e0b` - Warning/caution states
- **Error**: `#ef4444` - Error/danger states
- **Info**: `#38bdf8` - Information/notice states

### Background Colors
- **Surface**: `#f6f8fb` - Main background (Soft Blue Gray)
- **Card**: `#ffffff` - Card/surface background
- **Secondary Surface**: `#f1f3f7` - Secondary background
- **Elevated Surface**: `#fcfdff` - Elevated background for modals
- **Divider**: `#e5e7eb` - Border color

### Text Colors
- **Text Primary**: `#2d3748` - Main text color
- **Text Secondary**: `#6b7280` - Secondary text color
- **Text Light**: `#b0b7c3` - Light text for hints
- **Text Muted**: `#9ca3af` - Muted text for metadata
- **Text On Primary**: `#ffffff` - Text on primary background
- **Text On Accent**: `#1f2937` - Text on accent background

## UI Components

### Button
Reusable button component with multiple variants.

```tsx
import { Button } from '@/components';

// Usage
<Button variant="primary">Click me</Button>
<Button variant="secondary" size="lg" fullWidth>
  Full Width Button
</Button>
<Button loading>Loading...</Button>
<Button disabled>Disabled</Button>
```

**Props:**
- `variant`: 'primary' | 'secondary' | 'accent' | 'danger' | 'ghost'
- `size`: 'sm' | 'md' | 'lg'
- `fullWidth`: boolean
- `loading`: boolean
- All standard `HTMLButtonElement` props

### Card
Card container for grouping content.

```tsx
import { Card, CardHeader, CardContent, CardFooter } from '@/components';

<Card elevated>
  <CardHeader>
    <h2>Card Title</h2>
  </CardHeader>
  <CardContent>
    <p>Card content goes here</p>
  </CardContent>
  <CardFooter>
    <Button>Action</Button>
  </CardFooter>
</Card>
```

**Props:**
- `elevated`: boolean - adds shadow

### Input
Text input field with label and error support.

```tsx
import { Input, Textarea } from '@/components';

<Input
  label="Name"
  placeholder="Enter name"
  error="This field is required"
  helperText="Helper text"
/>

<Textarea
  label="Description"
  rows={4}
/>
```

**Props:**
- `label`: string
- `error`: string
- `helperText`: string
- All standard `HTMLInputElement` props

### Badge
Small label component for status or categories.

```tsx
import { Badge } from '@/components';

<Badge variant="primary">Active</Badge>
<Badge variant="success" size="md">Success</Badge>
```

**Props:**
- `variant`: 'primary' | 'secondary' | 'accent' | 'success' | 'warning' | 'error' | 'info'
- `size`: 'sm' | 'md'

### Alert
Dismissible alert message component.

```tsx
import { Alert } from '@/components';

<Alert type="success" title="Success!" dismissible>
  Operation completed successfully.
</Alert>

<Alert type="error">
  An error occurred. Please try again.
</Alert>
```

**Props:**
- `type`: 'success' | 'warning' | 'error' | 'info'
- `title`: string (optional)
- `dismissible`: boolean
- `onDismiss`: callback function

## Tailwind Classes

### Apply theme colors using Tailwind classes:

```tsx
// Background
<div className="bg-primary">Primary background</div>
<div className="bg-secondary">Secondary background</div>
<div className="bg-surface">Surface background</div>

// Text colors
<p className="text-text-primary">Primary text</p>
<p className="text-text-secondary">Secondary text</p>
<p className="text-text-muted">Muted text</p>

// Borders
<div className="border border-divider">Bordered element</div>
<input className="border-input-border focus:border-input-focus-border" />

// Status colors
<div className="text-success">Success</div>
<div className="text-error">Error</div>
<div className="text-warning">Warning</div>
```

## Spacing System

The theme uses a consistent spacing scale:
- `xs`: 4px
- `sm`: 8px
- `md`: 12px
- `lg`: 16px
- `xl`: 24px
- `2xl`: 32px
- `3xl`: 48px

## Border Radius

- Default: 12px
- Small: 8px
- Medium: 12px
- Large: 16px
- Extra Large: 20px
- Full: 9999px

## Using the Theme in Components

```tsx
import { Button, Card, CardContent, Input, Badge, Alert } from '@/components';

export default function MyComponent() {
  return (
    <Card elevated>
      <CardContent className="space-y-4">
        <h2 className="text-2xl font-bold text-text-primary">
          Example Component
        </h2>
        
        <Input
          label="Email"
          type="email"
          placeholder="your@email.com"
        />
        
        <Badge variant="primary">Active</Badge>
        
        <Alert type="info">
          This is an informational message.
        </Alert>
        
        <div className="flex gap-2">
          <Button variant="primary">Save</Button>
          <Button variant="ghost">Cancel</Button>
        </div>
      </CardContent>
    </Card>
  );
}
```

## Font Family

The theme uses Poppins as the primary font family, with a fallback to system fonts:
- `font-poppins` for explicit Poppins usage
- `font-sans` for default sans-serif

## Animations

The theme includes smooth transitions by default:
- Fade in: `animate-fade-in`
- Slide up: `animate-slide-up`
- Pulse: `animate-pulse-soft`

```tsx
<div className="animate-fade-in">Fading in</div>
<div className="animate-slide-up">Sliding up</div>
```

## Category Colors

For categorizing content:
- **Academics**: `#3a7bd5` (Primary Blue)
- **Hostel**: `#6bcb77` (Community Green)
- **Facilities**: `#4caf50` (Success Green)
- **Food**: `#ffb84c` (Friendly Orange)
- **Career**: `#8b5cf6` (Purple)
- **Events**: `#f59e0b` (Amber)
- **General**: `#6b7280` (Muted Gray)

## Responsive Design

The theme fully supports Tailwind's responsive utilities:

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
  {/* Grid adapts based on screen size */}
</div>
```

## Best Practices

1. **Always use color variables** instead of hardcoding hex values
2. **Use Tailwind classes** for styling instead of inline styles
3. **Leverage component composition** for consistent UI
4. **Maintain spacing consistency** using the defined scale
5. **Use semantic color meanings** (success, error, warning, info)
6. **Keep accessibility in mind** with proper contrast ratios
