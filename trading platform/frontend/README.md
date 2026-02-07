# Trading Analytics Platform - Frontend

React + TypeScript frontend with TradingView Lightweight Charts.

## Setup

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Copy environment variables:
```bash
cp .env.example .env
```

3. Edit `.env` and configure your settings

### Running the Application

Start the development server:
```bash
npm run dev
```

The application will be available at http://localhost:3000

### Building for Production

Build the application:
```bash
npm run build
```

Preview the production build:
```bash
npm run preview
```

### Running Tests

Run all tests:
```bash
npm test
```

Run tests with UI:
```bash
npm run test:ui
```

Run tests with coverage:
```bash
npm run test:coverage
```

### Linting

Run ESLint:
```bash
npm run lint
```

## Project Structure

```
frontend/
├── src/
│   ├── components/      # React components
│   ├── lib/            # Utilities and API client
│   ├── types/          # TypeScript type definitions
│   ├── test/           # Test utilities
│   ├── App.tsx         # Main application component
│   ├── main.tsx        # Application entry point
│   └── index.css       # Global styles
├── public/             # Static assets
├── index.html          # HTML template
├── package.json        # Dependencies and scripts
├── tsconfig.json       # TypeScript configuration
├── vite.config.ts      # Vite configuration
└── .env.example        # Example environment variables
```

## Key Technologies

- **React 18**: UI framework
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool and dev server
- **TradingView Lightweight Charts**: Professional charting library
- **React Query**: Data fetching and caching
- **Zustand**: State management
- **Axios**: HTTP client
- **Vitest**: Testing framework
- **Fast-check**: Property-based testing

## Development

### Code Style

- Use TypeScript for all components and utilities
- Follow React best practices and hooks guidelines
- Use functional components with hooks
- Write tests for all components and utilities

### Component Structure

Components should follow this structure:
```tsx
import { FC } from 'react'
import './ComponentName.css'

interface ComponentNameProps {
  // Props interface
}

export const ComponentName: FC<ComponentNameProps> = ({ prop1, prop2 }) => {
  // Component logic
  
  return (
    // JSX
  )
}
```

### State Management

- Use React Query for server state
- Use Zustand for client state
- Use local state (useState) for component-specific state

### API Integration

All API calls should go through the `apiClient` in `src/lib/api.ts`:

```tsx
import { apiClient } from '@/lib/api'

const data = await apiClient.get('/api/v1/instruments')
```

## Testing

### Unit Tests

Write unit tests for:
- Component rendering
- User interactions
- Utility functions
- API client methods

### Property-Based Tests

Use fast-check for property-based testing:
```tsx
import fc from 'fast-check'

test('property test example', () => {
  fc.assert(
    fc.property(fc.integer(), (n) => {
      // Property assertion
    })
  )
})
```

## Deployment

The frontend can be deployed to any static hosting service:
- Vercel
- Netlify
- AWS S3 + CloudFront
- GitHub Pages

Build the application and deploy the `dist` folder.
