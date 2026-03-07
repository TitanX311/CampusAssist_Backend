/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Professional Neutral Palette (Slate-based)
        neutral: {
          0: '#ffffff',
          50: '#f8fafc',
          100: '#f1f5f9',
          150: '#e8ecf1',
          200: '#e2e8f0',
          250: '#cbd5e1',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          750: '#293548',
          800: '#1e293b',
          850: '#1a2332',
          900: '#0f172a',
          950: '#020617',
        },
        
        // Professional Primary - Indigo/Blue
        primary: {
          25: '#faf9fd',
          50: '#f5f3ff',
          100: '#ede9fe',
          150: '#ddd6fe',
          200: '#e0e7ff',
          300: '#c7d2fe',
          400: '#a5b4fc',
          500: '#818cf8',
          600: '#4f46e5', // Main - Professional Indigo
          700: '#4338ca', // Hover
          800: '#3730a3', // Active
          900: '#312e81',
        },
        
        // Professional Secondary - Teal/Emerald
        secondary: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#14b8a6', // Main - Emerald
          600: '#0d9488', // Hover
          700: '#047857', // Active
          800: '#065f46',
          900: '#034e3f',
        },
        
        // Professional Accent - Amber/Gold (more refined)
        accent: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b', // Main - Amber
          600: '#d97706', // Hover
          700: '#b45309', // Active
          800: '#92400e',
          900: '#78350f',
        },
        
        // Semantic Colors - Professional
        success: {
          light: '#d1fae5',
          DEFAULT: '#10b981',
          dark: '#059669',
          darker: '#047857',
        },
        warning: {
          light: '#fef3c7',
          DEFAULT: '#f59e0b',
          dark: '#d97706',
          darker: '#b45309',
        },
        error: {
          light: '#fee2e2',
          DEFAULT: '#ef4444',
          dark: '#dc2626',
          darker: '#b91c1c',
        },
        info: {
          light: '#dbeafe',
          DEFAULT: '#0ea5e9',
          dark: '#0284c7',
          darker: '#0369a1',
        },
        
        // Light Theme - Professional Palette
        'bg-primary': '#ffffff',
        'bg-secondary': '#f8fafc',
        'bg-tertiary': '#f1f5f9',
        'bg-hover': '#f0f4f8',
        'border-primary': '#e2e8f0',
        'border-secondary': '#cbd5e1',
        'border-subtle': '#f1f5f9',
        'text-primary': '#0f172a',
        'text-secondary': '#475569',
        'text-tertiary': '#64748b',
        
        // Dark Theme - Professional Palette
        'dark-bg-primary': '#0f172a',
        'dark-bg-secondary': '#1a2332',
        'dark-bg-tertiary': '#293548',
        'dark-bg-hover': '#334155',
        'dark-border-primary': '#334155',
        'dark-border-secondary': '#475569',
        'dark-border-subtle': '#1e293b',
        'dark-text-primary': '#f8fafc',
        'dark-text-secondary': '#cbd5e1',
        'dark-text-tertiary': '#94a3b8',
      },
      fontFamily: {
        sans: ['ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', '"Helvetica Neue"', 'Arial', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', '"SF Mono"', 'Consolas', '"Liberation Mono"', 'Menlo', 'monospace'],
      },
      fontSize: {
        xs: ['12px', { lineHeight: '16px', fontWeight: '400' }],
        sm: ['13px', { lineHeight: '20px', fontWeight: '400' }],
        base: ['14px', { lineHeight: '22px', fontWeight: '400' }],
        lg: ['16px', { lineHeight: '24px', fontWeight: '500' }],
        xl: ['18px', { lineHeight: '28px', fontWeight: '600' }],
        '2xl': ['22px', { lineHeight: '32px', fontWeight: '700' }],
        '3xl': ['28px', { lineHeight: '36px', fontWeight: '700' }],
        '4xl': ['36px', { lineHeight: '44px', fontWeight: '700' }],
      },
      fontWeight: {
        ultralight: '100',
        thin: '200',
        light: '300',
        normal: '400',
        medium: '500',
        semibold: '600',
        bold: '700',
        extrabold: '800',
        black: '900',
      },
      letterSpacing: {
        tighter: '-0.02em',
        tight: '-0.01em',
        normal: '0',
        wide: '0.01em',
      },
      borderRadius: {
        none: '0',
        xs: '4px',
        sm: '6px',
        DEFAULT: '8px',
        md: '10px',
        lg: '12px',
        xl: '16px',
        '2xl': '20px',
        full: '9999px',
      },
      boxShadow: {
        xs: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05), 0 1px 3px 0 rgba(0, 0, 0, 0.1)',
        DEFAULT: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.05)',
        none: 'none',
        
        // Professional elevation shadows
        'elevation-1': '0 1px 3px 0 rgba(0, 0, 0, 0.08)',
        'elevation-2': '0 4px 8px -2px rgba(0, 0, 0, 0.1)',
        'elevation-3': '0 8px 16px -2px rgba(0, 0, 0, 0.12)',
      },
      spacing: {
        xs: '4px',
        sm: '8px',
        md: '12px',
        lg: '16px',
        xl: '24px',
        '2xl': '32px',
        '3xl': '48px',
        '4xl': '64px',
      },
      transitionDuration: {
        '100': '100ms',
        '200': '200ms',
        '300': '300ms',
        '400': '400ms',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(8px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.6' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
};

