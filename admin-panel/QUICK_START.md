# Quick Start Guide - Campus Assist Theme

## 🚀 Getting Started

### 1. Install Dependencies
```bash
npm install
```

### 2. Start Development Server
```bash
npm run dev
```

Then open [http://localhost:3000](http://localhost:3000) in your browser.

### 3. View Theme Components
The home page showcases all available components and theme colors.

---

## 📦 Using Components

### Import Components
```tsx
import { Button, Card, Input, Badge, Alert } from '@/components';
import { AdminLayout } from '@/components/AdminLayout';
```

### Basic Example
```tsx
export default function MyPage() {
  return (
    <AdminLayout>
      <Card>
        <CardHeader>
          <h1 className="text-2xl font-bold">Welcome</h1>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input label="Name" placeholder="Enter your name" />
          <Button fullWidth variant="primary">Save</Button>
        </CardContent>
      </Card>
    </AdminLayout>
  );
}
```

---

## 🎨 Color System

### Primary Brand Colors
```tsx
// Blue (Primary)
className="bg-primary text-primary"

// Green (Secondary)
className="bg-secondary text-secondary"

// Orange (Accent)
className="bg-accent text-accent"
```

### Status Colors
```tsx
// Success
<Badge variant="success">Active</Badge>

// Warning
<Badge variant="warning">Pending</Badge>

// Error
<Badge variant="error">Failed</Badge>

// Info
<Badge variant="info">Notice</Badge>
```

### Text Colors
```tsx
<p className="text-text-primary">Main text</p>
<p className="text-text-secondary">Secondary text</p>
<p className="text-text-light">Light text</p>
<p className="text-text-muted">Muted text</p>
```

---

## 🔘 Button Examples

```tsx
// Primary Button
<Button variant="primary">Primary</Button>

// Secondary Button
<Button variant="secondary">Secondary</Button>

// Accent Button
<Button variant="accent">Accent</Button>

// Danger Button
<Button variant="danger">Delete</Button>

// Ghost Button (outlined)
<Button variant="ghost">Cancel</Button>

// Different Sizes
<Button size="sm">Small</Button>
<Button size="md">Medium</Button>
<Button size="lg">Large</Button>

// Full Width
<Button fullWidth>Full Width Button</Button>

// Loading State
<Button loading>Processing...</Button>

// Disabled
<Button disabled>Disabled</Button>
```

---

## 📝 Form Elements

```tsx
import { Input, Textarea } from '@/components';

// Text Input
<Input
  label="Email"
  type="email"
  placeholder="Enter your email"
  value={email}
  onChange={(e) => setEmail(e.target.value)}
/>

// Input with Helper Text
<Input
  label="Password"
  type="password"
  helperText="Minimum 8 characters"
/>

// Input with Error
<Input
  label="Username"
  error="This username is already taken"
/>

// Textarea
<Textarea
  label="Description"
  placeholder="Enter description"
  rows={4}
/>
```

---

## 🏷️ Badge & Alert Examples

```tsx
import { Badge, Alert } from '@/components';

// Badges
<Badge variant="primary">Tag</Badge>
<Badge variant="secondary" size="md">Active</Badge>
<Badge variant="success">Verified</Badge>

// Alerts
<Alert type="success" title="Success!" dismissible>
  Operation completed successfully.
</Alert>

<Alert type="warning">
  This action cannot be undone.
</Alert>

<Alert type="error" title="Error">
  Something went wrong. Please try again.
</Alert>

<Alert type="info">
  For your information.
</Alert>
```

---

## 📊 Card Layout

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
    <Button variant="primary">Action</Button>
  </CardFooter>
</Card>
```

---

## 🎯 Using Tailwind Classes

### Spacing
```tsx
<div className="p-4">Padding (16px)</div>
<div className="gap-3">Gap between items (12px)</div>
<div className="mb-6">Margin bottom (24px)</div>
```

### Grid Layout
```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
  {/* Items */}
</div>
```

### Flexbox
```tsx
<div className="flex items-center justify-between gap-4">
  {/* Items */}
</div>
```

### Responsive
```tsx
<div className="text-lg md:text-2xl lg:text-3xl">
  Responsive text size
</div>
```

### Borders
```tsx
<div className="border border-divider rounded-lg">
  Bordered element
</div>
```

### Shadows
```tsx
<div className="shadow-sm">Light shadow</div>
<div className="shadow-lg">Large shadow</div>
```

---

## 🎨 Custom Color Utilities

### Using Tailwind Color Classes
```tsx
// Background colors
<div className="bg-primary-50">Light primary</div>
<div className="bg-primary-500">Primary</div>
<div className="bg-primary-900">Dark primary</div>

// Text colors
<p className="text-primary-600">Colored text</p>

// Border colors
<div className="border-primary-200">Colored border</div>
```

---

## 📱 Responsive Design

Use Tailwind's responsive prefixes:
```tsx
<div className="w-full md:w-1/2 lg:w-1/3">
  Responsive width
</div>

<div className="flex flex-col md:flex-row gap-4">
  Responsive direction
</div>

<div className="text-center md:text-left">
  Responsive text alignment
</div>
```

---

## ⚡ Animations

Built-in animations:
```tsx
<div className="animate-fade-in">Fading in</div>
<div className="animate-slide-up">Sliding up</div>
<div className="animate-pulse-soft">Pulsing</div>
```

---

## 🔧 Customization

### Edit Theme Colors
Update `tailwind.config.js`:
```js
colors: {
  primary: '#your-color',
  secondary: '#your-color',
  // ... more colors
}
```

### Add Custom Classes
Add to `app/globals.css`:
```css
@layer components {
  .custom-button {
    @apply px-4 py-2 rounded-lg font-semibold transition-all;
  }
}
```

---

## 📚 Documentation

- **Full Theme Guide**: See `THEME_GUIDE.md`
- **Implementation Details**: See `UI_IMPLEMENTATION.md`
- **Component Examples**: Check `app/page.tsx`

---

## 🚢 Building for Production

```bash
npm run build
npm start
```

---

## ❓ Common Questions

**Q: How do I use custom font sizes?**
A: Tailwind provides `text-sm`, `text-base`, `text-lg`, etc. Or add custom sizes in `tailwind.config.js`.

**Q: Can I override component styles?**
A: Yes! Pass additional `className` prop or use Tailwind utilities.

**Q: How do I add dark mode?**
A: Update the dark mode colors in `tailwind.config.js` and add `dark:` prefixes to classes.

**Q: Are animations customizable?**
A: Yes, edit the `keyframes` in `tailwind.config.js`.

---

## 💡 Tips

1. Always use Tailwind classes instead of inline styles
2. Maintain the spacing scale for consistency
3. Use semantic color meanings (success, error, warning, info)
4. Leverage component composition for DRY code
5. Check `THEME_GUIDE.md` for all available utilities

---

**Happy Coding! 🎉**
