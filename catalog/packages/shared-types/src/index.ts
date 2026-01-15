/**
 * Shared types package for frontend and backend
 * 
 * This package provides type definitions that are shared between
 * the frontend and backend to ensure type safety and consistency.
 * 
 * Structure:
 * - Enums: Shared enums
 * - DTOs: API response types (camelCase) - for frontend/API layer
 * - Internal: Database model types (snake_case) - for backend repositories/services
 */

// Enums (shared)
export * from './enums';

// API responses (DTOs - camelCase)
export * from './api-responses';
export * from './product'; // ProductDto, CreateProductDto
export * from './auth'; // UserDto, AuthResponseDto
export * from './article'; // ArticleDto
export * from './review'; // ReviewDto

// Internal types (snake_case - for backend)
export * from './user'; // User, CreateUserInput, SellerApplication
export * from './persona'; // Persona, CreatePersonaInput, UpdatePersonaInput
export * from './article-internal'; // Article, CreateArticleInput
export * from './summary'; // Summary, CreateSummaryInput
export * from './schedule'; // FetchSchedule, CreateScheduleInput
export * from './tool'; // ToolRequest, CreateToolRequestInput (ToolRequestStatus from enums)
export * from './product-internal'; // Product, CreateProductInput, UpdateProductInput, ProductQueryFilters
export * from './product-artifact'; // ProductArtifact, ProductArtifactDto, CreateProductArtifactInput
export * from './product-workflow'; // ProductWorkflow, ProductWorkflowDto, CreateProductWorkflowInput
export * from './product-review-audit'; // ProductReviewAuditLog, ProductReviewAuditLogDto
export * from './review-internal'; // Review, CreateReviewInput, UpdateReviewInput, ReviewQueryFilters
export * from './auth-internal'; // JWTPayload, LoginInput, RegisterInput, ChatMessage, ChatRequest

// Error types
export * from './errors';

