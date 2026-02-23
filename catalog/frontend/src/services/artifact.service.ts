import { apiClient } from '@/shared/api/client';
import { ArtifactType } from '@gsnake/shared-types';

export interface ProductArtifact {
  id: string;
  productId: string;
  artifactType: ArtifactType;
  fileName: string;
  fileUrl: string;
  fileSize: number | null;
  mimeType: string | null;
  checksum: string | null;
  version: string | null;
  isPrimary: boolean;
  metadata: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

class ArtifactService {
  /**
   * Upload artifact file for a product
   */
  async uploadArtifact(
    productId: string,
    file: File,
    artifactType: ArtifactType,
    options?: { version?: string; isPrimary?: boolean }
  ): Promise<ProductArtifact> {
    const formData = new FormData();
    formData.append('file', file);
    const versionParam = options?.version ? `&version=${encodeURIComponent(options.version)}` : '';
    const primaryParam = options?.isPrimary !== undefined ? `&is_primary=${options.isPrimary}` : '';

    const response = await apiClient.post<{ artifact: ProductArtifact }>(
      `/products/${productId}/artifacts/upload?artifact_type=${artifactType}${versionParam}${primaryParam}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.artifact;
  }

  /**
   * Get all artifacts for a product
   */
  async getArtifacts(productId: string): Promise<ProductArtifact[]> {
    const response = await apiClient.get<{ artifacts: ProductArtifact[] }>(
      `/products/${productId}/artifacts`
    );
    return response.artifacts;
  }

  /**
   * Delete an artifact
   */
  async deleteArtifact(productId: string, artifactId: string): Promise<void> {
    await apiClient.delete(`/products/${productId}/artifacts/${artifactId}`);
  }
}

export default new ArtifactService();

