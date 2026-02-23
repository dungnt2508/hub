# Shared Types Usage Guide

## Overview

The `@gsnake/shared-types` package provides TypeScript type definitions that are shared between the frontend and backend to ensure type safety and consistency across the application.

## Installation

The package is already installed in both `backend` and `frontend` as a local dependency.

## Structure

```
packages/shared-types/
├── src/
│   ├── enums.ts          # Shared enums (UserRole, ProductType, etc.)
│   ├── api-responses.ts  # Standard API response structures
│   ├── product.ts       # Product-related types
│   ├── auth.ts          # Auth-related types
│   ├── article.ts       # Article-related types
│   ├── errors.ts        # Error types and codes
│   └── index.ts         # Main export file
```

## Usage Examples

### Backend

```typescript
import { ProductDto, UserDto, ERROR_CODES } from '@gsnake/shared-types';

// In DTOs
export type { ProductDto } from '@gsnake/shared-types';

// In mappers
import { ProductDto } from '@gsnake/shared-types';
static toResponseDto(product: Product): ProductDto { ... }
```

### Frontend

```typescript
import { ProductDto, UserDto, ProductFilters } from '@gsnake/shared-types';

// In services
async getProducts(filters: ProductFilters): Promise<ProductDto[]> { ... }
```

## Type Naming Conventions

- **DTOs**: Use camelCase (e.g., `ProductDto`, `UserDto`)
- **Enums**: PascalCase (e.g., `ProductType`, `UserRole`)
- **Input types**: Use `Dto` suffix (e.g., `CreateProductDto`, `UpdateProductDto`)

## Adding New Types

1. Add the type definition to the appropriate file in `src/`
2. Export it from `src/index.ts`
3. Run `npm run build` to compile
4. Both frontend and backend will automatically pick up the new types

## Development Workflow

1. Make changes to types in `packages/shared-types/src/`
2. Run `npm run build` in the shared-types directory
3. Frontend and backend will use the updated types automatically (no need to reinstall)

## Notes

- All API responses use **camelCase** (matching DTOs)
- Database models use **snake_case** (handled by mappers)
- Frontend services convert between camelCase (DTOs) and snake_case (API) as needed

