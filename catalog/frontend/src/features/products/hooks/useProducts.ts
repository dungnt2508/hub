import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import productService from '@/services/product.service';
import { ProductFilters, ProductDto, ProductsResponse, CreateProductDto, UpdateProductDto } from '@gsnake/shared-types';

/**
 * Get all products with filters
 */
export function useProducts(filters: ProductFilters = {}) {
    return useQuery({
        queryKey: ['products', filters],
        queryFn: () => productService.getProducts(filters),
        staleTime: 1000 * 60 * 5, // 5 minutes
    });
}

/**
 * Get product by ID
 */
export function useProduct(id: string) {
    return useQuery({
        queryKey: ['product', id],
        queryFn: () => productService.getProduct(id),
        enabled: !!id,
        staleTime: 1000 * 60 * 5,
    });
}

/**
 * Get seller's products
 */
export function useMyProducts(includeDrafts: boolean = true) {
    return useQuery({
        queryKey: ['products', 'my', includeDrafts],
        queryFn: () => productService.getMyProducts(includeDrafts),
        staleTime: 1000 * 60 * 2, // 2 minutes for own products
    });
}

/**
 * Get seller's product by ID
 */
export function useMyProduct(id: string) {
    return useQuery({
        queryKey: ['product', 'my', id],
        queryFn: () => productService.getMyProduct(id),
        enabled: !!id,
    });
}

/**
 * Get featured products
 */
export function useFeaturedProducts(limit: number = 6) {
    return useQuery({
        queryKey: ['products', 'featured', limit],
        queryFn: () => productService.getFeaturedProducts(limit),
        staleTime: 1000 * 60 * 10, // 10 minutes for featured
    });
}

/**
 * Create product mutation
 */
export function useCreateProduct() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: CreateProductDto) => productService.createProduct(data),
        onSuccess: () => {
            // Invalidate and refetch
            queryClient.invalidateQueries({ queryKey: ['products'] });
        },
    });
}

/**
 * Update product mutation
 */
export function useUpdateProduct() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, data }: { id: string; data: UpdateProductDto }) =>
            productService.updateProduct(id, data),
        onSuccess: (data, variables) => {
            // Invalidate queries
            queryClient.invalidateQueries({ queryKey: ['products'] });
            queryClient.invalidateQueries({ queryKey: ['product', variables.id] });
            queryClient.invalidateQueries({ queryKey: ['product', 'my', variables.id] });
        },
    });
}

/**
 * Delete product mutation
 */
export function useDeleteProduct() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (id: string) => productService.deleteProduct(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['products'] });
        },
    });
}

/**
 * Publish product mutation
 */
export function usePublishProduct() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (id: string) => productService.publishProduct(id),
        onSuccess: (data, id) => {
            queryClient.invalidateQueries({ queryKey: ['products'] });
            queryClient.invalidateQueries({ queryKey: ['product', id] });
            queryClient.invalidateQueries({ queryKey: ['product', 'my', id] });
        },
    });
}

/**
 * Unpublish product mutation
 */
export function useUnpublishProduct() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (id: string) => productService.unpublishProduct(id),
        onSuccess: (data, id) => {
            queryClient.invalidateQueries({ queryKey: ['products'] });
            queryClient.invalidateQueries({ queryKey: ['product', id] });
            queryClient.invalidateQueries({ queryKey: ['product', 'my', id] });
        },
    });
}

