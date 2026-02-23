# @gsnake/shared-types

Shared TypeScript types for frontend and backend applications.

## Installation

This package is used as a local dependency in the monorepo.

### From backend:
```bash
cd backend
npm install ../packages/shared-types
```

### From frontend:
```bash
cd frontend
npm install ../packages/shared-types
```

## Building

```bash
npm run build
```

This will compile TypeScript to JavaScript and generate type definitions in the `dist/` directory.

## Usage

```typescript
import { ProductDto, UserDto, ERROR_CODES } from '@gsnake/shared-types';
```

## Development

Watch mode for development:
```bash
npm run watch
```

