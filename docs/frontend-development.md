# Frontend Development Guidelines

When frontend code is added to this repository, follow these guidelines to integrate with the CI/CD pipeline:

## Directory Structure

```
frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── utils/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── package.json
├── tsconfig.json (if using TypeScript)
└── README.md
```

## Package.json Scripts

Add these scripts to your `package.json`:

```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "lint": "eslint src/ tests/",
    "lint:fix": "eslint src/ tests/ --fix",
    "format": "prettier --write src/ tests/",
    "format:check": "prettier --check src/ tests/",
    "build": "vite build",
    "dev": "vite dev",
    "preview": "vite preview"
  }
}
```

## Enabling Frontend Tests in CI

To enable frontend tests, uncomment and modify the frontend-tests job in `.github/workflows/ci.yml`:

```yaml
frontend-tests:
  runs-on: ubuntu-latest
  
  steps:
  - uses: actions/checkout@v4
  
  - name: Setup Node.js
    uses: actions/setup-node@v4
    with:
      node-version: '18'
      cache: 'npm'  # or 'yarn' depending on package manager
  
  - name: Install frontend dependencies
    run: npm ci  # or yarn install --frozen-lockfile
  
  - name: Run frontend tests
    run: npm test  # or yarn test
  
  - name: Run frontend linting
    run: npm run lint  # or yarn lint
  
  - name: Check frontend formatting
    run: npm run format:check
  
  - name: Build frontend
    run: npm run build
```

## Required Status Checks

After adding frontend tests, update the branch protection rules to include:
- `frontend-tests` - Frontend testing job

## Recommended Frontend Tools

- **Framework**: React, Vue, or Svelte
- **Build Tool**: Vite or Webpack
- **Testing**: Jest + Testing Library
- **Linting**: ESLint + Prettier
- **Type Checking**: TypeScript (recommended)

## Example Test Structure

```javascript
// tests/unit/component.test.js
import { render, screen } from '@testing-library/react';
import MyComponent from '../src/components/MyComponent';

test('renders component correctly', () => {
  render(<MyComponent />);
  expect(screen.getByText('Hello World')).toBeInTheDocument();
});
```