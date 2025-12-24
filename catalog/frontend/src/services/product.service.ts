import { apiClient } from '@/shared/api/client';
import { 
  ProductDto as Product, 
  CreateProductDto as CreateProductInput,
  UpdateProductDto as UpdateProductInput,
  ProductFilters,
  ProductsResponse
} from '@gsnake/shared-types';

// Re-export types for convenience
export type { 
  Product, 
  CreateProductInput, 
  UpdateProductInput, 
  ProductFilters, 
  ProductsResponse 
};

class ProductService {
  /**
   * Get all products with filters
   */
  async getProducts(filters: ProductFilters = {}): Promise<ProductsResponse> {
    const params = new URLSearchParams();
    
    if (filters.type) params.append('type', filters.type);
    if (filters.search) params.append('search', filters.search);
    if (filters.tags && filters.tags.length > 0) params.append('tags', filters.tags.join(','));
    if (filters.seller_id) params.append('seller_id', filters.seller_id);
    if (filters.price_type) params.append('price_type', filters.price_type);
    if (filters.is_free !== undefined) params.append('is_free', String(filters.is_free));
    if (filters.limit) params.append('limit', filters.limit.toString());
    if (filters.offset) params.append('offset', filters.offset.toString());
    if (filters.sort_by) params.append('sort_by', filters.sort_by);
    if (filters.sort_order) params.append('sort_order', filters.sort_order);

    // apiClient.get() already unwraps response.data, so response is already the data
    const response = await apiClient.get<ProductsResponse>(`/products?${params.toString()}`);
    return response;
  }

  /**
   * Get featured products
   */
  async getFeaturedProducts(limit: number = 6): Promise<Product[]> {
    // apiClient.get() already unwraps response.data, so response is already the data
    const response = await apiClient.get<{ products: Product[] }>(`/products/featured?limit=${limit}`);
    return response.products;
  }

  /**
   * Get product by ID (public - only published)
   */
  async getProduct(id: string): Promise<Product> {
    // apiClient.get() already unwraps response.data, so response is already the data
    const response = await apiClient.get<{ product: Product }>(`/products/${id}`);
    return response.product;
  }

  /**
   * Get seller's own product by ID (can access drafts)
   */
  async getMyProduct(id: string): Promise<Product> {
    // apiClient.get() already unwraps response.data, so response is already the data
    const response = await apiClient.get<{ product: Product }>(`/products/my/${id}`);
    return response.product;
  }

  /**
   * Get seller's products
   */
  async getMyProducts(includeDrafts: boolean = true): Promise<Product[]> {
    // apiClient.get() already unwraps response.data, so response is already the data
    const response = await apiClient.get<{ products: Product[] }>(`/products/my?include_drafts=${includeDrafts}`);
    return response.products;
  }

  /**
   * Create new product
   * Note: Backend expects snake_case, so we convert camelCase to snake_case
   */
  async createProduct(data: CreateProductInput): Promise<Product> {
    // Convert camelCase to snake_case for backend
    const backendData = {
      title: data.title,
      description: data.description,
      long_description: data.longDescription,
      type: data.type,
      tags: data.tags,
      workflow_file_url: data.workflowFileUrl,
      thumbnail_url: data.thumbnailUrl,
      preview_image_url: data.previewImageUrl,
      video_url: (data as any).videoUrl,
      contact_channel: (data as any).contactChannel,
      is_free: data.isFree,
      price: data.price,
      currency: (data as any).currency,
      price_type: (data as any).priceType,
      version: data.version,
      requirements: data.requirements,
      features: data.features,
      install_guide: data.installGuide,
      metadata: data.metadata,
      // Phase 1 new fields
      changelog: (data as any).changelog,
      license: (data as any).license,
      author_contact: (data as any).authorContact,
      support_url: (data as any).supportUrl,
      screenshots: (data as any).screenshots,
      platform_requirements: (data as any).platformRequirements,
      required_credentials: (data as any).requiredCredentials,
      ownership_declaration: (data as any).ownershipDeclaration,
      ownership_proof_url: (data as any).ownershipProofUrl,
    };
    // apiClient.post() already unwraps response.data, so response is already the data
    const response = await apiClient.post<{ product: Product }>('/products', backendData);
    return response.product;
  }

  /**
   * Update product
   * Note: Backend expects snake_case, so we convert camelCase to snake_case
   */
  async updateProduct(id: string, data: UpdateProductInput): Promise<Product> {
    // Convert camelCase to snake_case for backend
    const backendData: any = {};
    if (data.title !== undefined) backendData.title = data.title;
    if (data.description !== undefined) backendData.description = data.description;
    if (data.longDescription !== undefined) backendData.long_description = data.longDescription;
    if (data.type !== undefined) backendData.type = data.type;
    if (data.tags !== undefined) backendData.tags = data.tags;
    if (data.workflowFileUrl !== undefined) backendData.workflow_file_url = data.workflowFileUrl;
    if (data.thumbnailUrl !== undefined) backendData.thumbnail_url = data.thumbnailUrl;
    if (data.previewImageUrl !== undefined) backendData.preview_image_url = data.previewImageUrl;
    if ((data as any).videoUrl !== undefined) backendData.video_url = (data as any).videoUrl;
    if ((data as any).contactChannel !== undefined) backendData.contact_channel = (data as any).contactChannel;
    if (data.isFree !== undefined) backendData.is_free = data.isFree;
    if (data.price !== undefined) backendData.price = data.price;
    if ((data as any).currency !== undefined) backendData.currency = (data as any).currency;
    if ((data as any).priceType !== undefined) backendData.price_type = (data as any).priceType;
    if (data.version !== undefined) backendData.version = data.version;
    if (data.requirements !== undefined) backendData.requirements = data.requirements;
    if (data.features !== undefined) backendData.features = data.features;
      if (data.installGuide !== undefined) backendData.install_guide = data.installGuide;
      if (data.metadata !== undefined) backendData.metadata = data.metadata;
      
      // Phase 1 new fields
      if ((data as any).changelog !== undefined) backendData.changelog = (data as any).changelog;
      if ((data as any).license !== undefined) backendData.license = (data as any).license;
      if ((data as any).authorContact !== undefined) backendData.author_contact = (data as any).authorContact;
      if ((data as any).supportUrl !== undefined) backendData.support_url = (data as any).supportUrl;
      if ((data as any).screenshots !== undefined) backendData.screenshots = (data as any).screenshots;
      if ((data as any).platformRequirements !== undefined) backendData.platform_requirements = (data as any).platformRequirements;
      if ((data as any).requiredCredentials !== undefined) backendData.required_credentials = (data as any).requiredCredentials;
      if ((data as any).ownershipDeclaration !== undefined) backendData.ownership_declaration = (data as any).ownershipDeclaration;
      if ((data as any).ownershipProofUrl !== undefined) backendData.ownership_proof_url = (data as any).ownershipProofUrl;
      
      // apiClient.put() already unwraps response.data, so response is already the data
      const response = await apiClient.put<{ product: Product }>(`/products/${id}`, backendData);
      return response.product;
  }

  /**
   * Delete product
   */
  async deleteProduct(id: string): Promise<void> {
    await apiClient.delete(`/products/${id}`);
  }

  /**
   * Publish product
   */
  async publishProduct(id: string): Promise<Product> {
    // apiClient.post() already unwraps response.data, so response is already the data
    const response = await apiClient.post<{ product: Product }>(`/products/${id}/publish`);
    return response.product;
  }

  /**
   * Unpublish product
   */
  async unpublishProduct(id: string): Promise<Product> {
    // apiClient.post() already unwraps response.data, so response is already the data
    const response = await apiClient.post<{ product: Product }>(`/products/${id}/unpublish`);
    return response.product;
  }

  /**
   * Record download
   */
  async recordDownload(id: string): Promise<void> {
    const response = await apiClient.post<{ downloadUrl: string }>(`/products/${id}/download`);
    if (response.downloadUrl) {
      window.open(response.downloadUrl, '_blank');
    }
  }
}

export default new ProductService();

