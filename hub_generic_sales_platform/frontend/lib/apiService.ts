"use client";

import axios, { AxiosInstance } from "axios";
import { Message } from "@/components/chat/ChatMessage";
import { useUIStore } from "./store";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8386/api/v1";

const DEV_FALLBACK_TENANT = "e13b1d92-755e-4c18-a91d-fd3cf27d04a5";

function getTenantId(): string | null {
    if (typeof window === "undefined") return null;
    const fromStore = useUIStore.getState().currentTenantId;
    if (fromStore) return fromStore;
    const fromStorage = localStorage.getItem("tenant_id");
    if (fromStorage) return fromStorage;
    if (process.env.NODE_ENV === "development") return DEV_FALLBACK_TENANT;
    return null;
}

// Create axios instance with default config
const createApiClient = (): AxiosInstance => {
    const client = axios.create({
        baseURL: API_BASE_URL,
        headers: {
            "Content-Type": "application/json",
        },
    });

    // Interceptor: X-Tenant-ID from store (sync with auth) -> localStorage -> dev fallback only
    client.interceptors.request.use((config) => {
        const tenantId = getTenantId();
        if (tenantId) {
            config.headers["X-Tenant-ID"] = tenantId;
        }

        const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
        if (token) {
            config.headers["Authorization"] = `Bearer ${token}`;
        }

        return config;
    });

    return client;
};

const apiClient = createApiClient();

export interface ChatResponse {
    response: string;
    session_id: string;
    metadata: {
        tier: string;
        cost: string;
        latency_ms: number;
        usage?: any;
        lifecycle_state?: string;  // Debug: current lifecycle state (X-Debug: true)
        tool_calls?: Array<{ name: string; args: Record<string, unknown>; success: boolean; elapsed_ms: number }>;
        g_ui?: {
            type: "bento_grid";
            data: {
                title: string;
                offerings: Array<{
                    id: string;
                    name: string;
                    price: string;
                    image?: string;
                    score?: number;
                    tags?: string[];
                }>;
            };
        };
    };
}

export interface Tenant {
    id: string;
    name: string;
    status: string;
    plan?: string;
    created_at: string;
}

export interface User {
    id: string;
    email: string;
    role: string;
    tenant_id: string;
    tenant_name?: string;
}

export interface LoginResponse {
    access_token: string;
    token_type: string;
    user: User;
}

export interface Bot {
    id: string;
    name: string;
    code: string;
    status: string;
    tenant_id: string;
    domain_id?: string;
    created_at: string;
    versions_count?: number;
    capabilities?: string[];
    domain?: KnowledgeDomain;
}

export interface Capability {
    id: string;
    code: string;
    description: string;
}

export interface DomainAttributeDefinition {
    id: string;
    domain_id: string;
    key: string;
    value_type: string;
    semantic_type?: string;
    scope: string;
    value_constraint?: any;
    // Note: tenant_id removed - this is global ontology, not tenant-scoped
}

export interface BotVersion {
    id: string;
    bot_id: string;
    version: number;
    is_active: boolean;
    capabilities: Capability[];
}

export interface SessionStats {
    session_id: string;
    summary: {
        total_turns: number;
        total_cost: string;
        avg_latency_ms: number;
    };
    timeline: Array<{
        tier: string;
        type: string;
        reason: string;
        cost: string;
        latency: number;
        usage: any;
        timestamp: string;
    }>;
}

export interface OfferingAttribute {
    id: string;
    offering_version_id: string;
    attribute_key: string;
    attribute_value: string;
    value_type: string;
    display_order: number;
}

export interface TenantOffering {
    id: string;
    tenant_id: string;
    domain_id: string;
    bot_id?: string;
    code: string;
    name: string;
    description?: string;
    status: string;
    created_at: string;
    updated_at?: string;
    attributes: OfferingAttribute[];
}

export interface InventoryStatus {
    tenant_id: string;
    offering_code: string;
    offering_name: string;
    sku: string;
    variant_name: string;
    location_code: string;
    aggregate_qty: number;
    aggregate_safety_stock: number;
    stock_status: string;
}

export interface InventoryLocation {
    id: string;
    tenant_id: string;
    code: string;
    name: string;

}

export interface OfferingPriceSummary {
    amount: number;
    currency: string;
    type: string;
    compare_at?: number;
    price_list_id?: string;
}

export interface CatalogOfferingVersion {
    id: string;
    offering_id: string;
    version: number;
    name: string;
    description?: string;
    status: string;
    created_at: string;
}

export interface OfferingVariant {
    id: string;
    offering_id: string;
    sku: string;
    name: string;
    status: string;
    created_at: string;
}

export interface VariantPrice {
    id: string;
    price_list_id: string;
    variant_id: string;
    currency: string;
    price_type: string;
    amount: number;
    compare_at?: number;
}

export interface KnowledgeDomain {
    id: string;
    code: string;
    name: string;
    description?: string;
    domain_type?: string;
    is_archived?: boolean;
    // Note: tenant_id removed - this is global ontology, not tenant-scoped
}

export interface FAQ {
    id: string;
    tenant_id: string;
    domain_id?: string;
    question: string;
    answer: string;
    category?: string;
    priority: number;
    is_active: boolean;
}

export interface UseCase {
    id: string;
    tenant_id: string;
    domain_id?: string;
    offering_id?: string;
    scenario: string;
    answer: string;
    priority: number;
    is_active: boolean;
}

export interface Comparison {
    id: string;
    tenant_id: string;
    domain_id?: string;
    title: string;
    description?: string;
    offering_ids: string[];
    comparison_data?: any;
    is_active: boolean;
}

export interface Guardrail {
    id: string;
    code: string;
    name: string;
    condition_expression: string;
    violation_action: string;
    fallback_message?: string;
    priority: number;
    is_active: boolean;
}

export interface MigrationJob {
    id: string;
    status: 'pending' | 'processing' | 'staged' | 'completed' | 'failed';
    source_type: 'web_scraper' | 'excel_upload' | 'shopify_sync' | 'haravan_sync';
    metadata: {
        url?: string;
        filename?: string;
    };
    staged_data?: any;
    error_log?: string;
    created_at: string;
    bot_id?: string | null;
    domain_id?: string | null;
}

export interface PriceList {
    id: string;
    tenant_id: string;
    channel_id?: string;
    code: string;
    valid_from?: string;
    valid_to?: string;
}

export interface SalesChannel {
    id: string;
    tenant_id: string;
    code: string;
    name: string;
    is_active: boolean;
}

export interface ChannelConfig {
    id: string;
    bot_version_id: string;
    channel_code: string;
    config?: Record<string, unknown>;
    is_active: boolean;
}

export interface OfferingSummary {
    id: string;
    code: string;
    bot_id?: string;
    name: string;
    description?: string;
    version: number;
    version_id: string;
    price?: OfferingPriceSummary;
    inventory: any[];
    status: string;
}

export interface Contact {
    id: string;
    name: string;
    email: string;
    phone?: string;
    status: 'active' | 'lead' | 'inactive';
    tags?: string[];
    last_active: string;
}

export interface SessionLog {
    id: string;
    bot_id: string;
    channel: string;
    total_turns: number;
    state: string;
    created_at: string;
    last_message?: string;
}

export interface SessionLogEntry {
    id: string;
    tenant_id: string;
    bot_id: string;
    bot_version_id: string;
    channel_code: string;
    lifecycle_state: string;
    started_at: string | null;
    ended_at: string | null;
    created_at: string | null;
}

export interface AnalyticsDashboard {
    summary: {
        total_savings: string;
        automation_rate: number;
        avg_latency: string;
        projected_growth: string;
        active_sessions?: number;
        total_sessions?: number;
    };
    tier_distribution?: Array<{ tier: string; count: number; percent: number }>;
    usage_mix: {
        model: string;
        percentage: number;
        color: string;
    }[];
    volume_history: number[];
    efficiency_trend: number[];
}

export const apiService = {
    // Chat API
    async sendMessage(
        tenantId: string,
        botId: string,
        message: string,
        sessionId?: string,
        options?: { debug?: boolean }
    ): Promise<ChatResponse> {
        const config = options?.debug ? { headers: { "X-Debug": "true" } } : {};
        const response = await apiClient.post<ChatResponse>("/chat/message", {
            message,
            bot_id: botId,
            session_id: sessionId,
        }, config);
        return response.data;
    },

    /** Widget chat (public, no JWT) - for embedded website */
    async sendWidgetMessage(tenantId: string, botId: string, message: string, sessionId?: string): Promise<ChatResponse> {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8386";
        const response = await fetch(`${baseUrl}/api/v1/chat/widget-message`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ tenant_id: tenantId, bot_id: botId, message, session_id: sessionId }),
        });
        if (!response.ok) throw new Error(await response.text());
        return response.json();
    },

    // Tenant Management
    async listTenants(): Promise<Tenant[]> {
        const response = await apiClient.get<Tenant[]>("/tenants");
        return response.data;
    },

    async createTenant(name: string): Promise<Tenant> {
        const response = await apiClient.post<Tenant>("/tenants", { name });
        return response.data;
    },

    async updateTenant(id: string, data: Partial<Tenant>): Promise<Tenant> {
        const response = await apiClient.put<Tenant>(`/tenants/${id}`, data);
        return response.data;
    },

    async deleteTenant(id: string): Promise<{ message: string }> {
        const response = await apiClient.delete<{ message: string }>(`/tenants/${id}`);
        return response.data;
    },

    async updateTenantStatus(id: string, status: string): Promise<Tenant> {
        const response = await apiClient.patch<Tenant>(`/tenants/${id}/status`, { status });
        return response.data;
    },

    // Bot Management
    async listBots(params?: { status?: string }): Promise<Bot[]> {
        const response = await apiClient.get<Bot[]>("/bots", { params });
        return response.data;
    },

    async createBot(name: string, code: string, domain_id?: string): Promise<Bot> {
        const response = await apiClient.post<Bot>("/bots", { name, code, domain_id });
        return response.data;
    },

    async updateBot(id: string, data: Partial<Bot>): Promise<Bot> {
        const response = await apiClient.put<Bot>(`/bots/${id}`, data);
        return response.data;
    },

    async deleteBot(id: string): Promise<{ message: string }> {
        const response = await apiClient.delete<{ message: string }>(`/bots/${id}`);
        return response.data;
    },

    async updateBotStatus(id: string, status: string): Promise<Bot> {
        const response = await apiClient.patch<Bot>(`/bots/${id}/status`, { status });
        return response.data;
    },

    // Bot Versions
    async listBotVersions(botId: string): Promise<BotVersion[]> {
        const response = await apiClient.get<BotVersion[]>(`/bots/${botId}/versions`);
        return response.data;
    },

    async createBotVersion(botId: string): Promise<BotVersion> {
        const response = await apiClient.post<BotVersion>(`/bots/${botId}/versions`);
        return response.data;
    },

    async activateBotVersion(botId: string, versionId: string): Promise<BotVersion> {
        const response = await apiClient.patch<BotVersion>(`/bots/${botId}/versions/${versionId}/activate`);
        return response.data;
    },

    // Bot Capabilities
    async listCapabilities(): Promise<Capability[]> {
        const response = await apiClient.get<Capability[]>("/capabilities");
        return response.data;
    },

    async updateBotVersionCapabilities(botId: string, versionId: string, capabilityCodes: string[]): Promise<BotVersion> {
        const response = await apiClient.patch<BotVersion>(`/bots/${botId}/versions/${versionId}/capabilities`, { codes: capabilityCodes });
        return response.data;
    },

    // Logs - Session list & turns
    async listSessions(params?: { bot_id?: string; channel_code?: string; active_only?: boolean; skip?: number; limit?: number }): Promise<SessionLogEntry[]> {
        const response = await apiClient.get<SessionLogEntry[]>("/sessions", { params });
        return response.data;
    },

    // Session Stats
    async getSessionStats(sessionId: string): Promise<SessionStats> {
        if (!sessionId?.trim()) {
            throw new Error("session_id is required");
        }
        const response = await apiClient.get<SessionStats>(`/sessions/${sessionId}/stats`);
        return response.data;
    },

    async getSessionState(sessionId: string): Promise<{ session_id: string; lifecycle_state: string; slots: { key: string; value: string; status: string }[] }> {
        const response = await apiClient.get(`/sessions/${sessionId}/state`);
        return response.data;
    },

    async getSessionTurns(sessionId: string): Promise<{ session_id: string; turns: { role: string; content: string; metadata?: any }[] }> {
        const response = await apiClient.get(`/sessions/${sessionId}/turns`);
        return response.data;
    },

    async handoverSession(sessionId: string): Promise<{ message: string; session_id: string; lifecycle_state: string }> {
        const response = await apiClient.post(`/sessions/${sessionId}/handover`);
        return response.data;
    },

    // Health Check
    async healthCheck(): Promise<{ status: string; version?: string }> {
        const response = await apiClient.get<{ status: string; version?: string }>("/health");
        return response.data;
    },

    // Authentication
    async login(credentials: { email: string; password: string }): Promise<LoginResponse> {
        const response = await apiClient.post<LoginResponse>("/auth/login", credentials);
        return response.data;
    },

    async getCurrentUser(): Promise<User> {
        const response = await apiClient.get<User>("/auth/me");
        return response.data;
    },

    async changePassword(current_password: string, new_password: string): Promise<{ message: string }> {
        const response = await apiClient.put<{ message: string }>("/auth/change-password", {
            current_password,
            new_password,
        });
        return response.data;
    },

    // Offering Catalog V4 (Enhanced)
    async listCatalogOfferings(channel: string = "WEB", bot_id?: string, domain_id?: string): Promise<OfferingSummary[]> {
        const response = await apiClient.get<OfferingSummary[]>("/catalog/offerings", {
            params: { channel, bot_id, domain_id }
        });
        return response.data;
    },

    async getCatalogOffering(code: string, channel: string = "WEB", bot_id?: string): Promise<OfferingSummary> {
        const response = await apiClient.get<OfferingSummary>(`/catalog/offerings/${code}`, {
            params: { channel, bot_id }
        });
        return response.data;
    },

    async listOfferingVersions(offeringId: string): Promise<CatalogOfferingVersion[]> {
        const response = await apiClient.get<CatalogOfferingVersion[]>(`/catalog/offerings/${offeringId}/versions`);
        return response.data;
    },

    async createOfferingVersion(offeringId: string): Promise<CatalogOfferingVersion> {
        const response = await apiClient.post<CatalogOfferingVersion>(`/catalog/offerings/${offeringId}/versions`);
        return response.data;
    },

    async updateOfferingVersion(versionId: string, data: { name?: string; description?: string }): Promise<CatalogOfferingVersion> {
        const response = await apiClient.put<CatalogOfferingVersion>(`/catalog/versions/${versionId}`, data);
        return response.data;
    },

    async deleteOfferingVersion(versionId: string): Promise<void> {
        await apiClient.delete(`/catalog/versions/${versionId}`);
    },

    async publishOfferingVersion(offeringId: string, version: number): Promise<{ message: string }> {
        const response = await apiClient.post<{ message: string }>(`/catalog/offerings/${offeringId}/publish`, null, {
            params: { version }
        });
        return response.data;
    },

    async getInventoryStatus(): Promise<InventoryStatus[]> {
        const response = await apiClient.get<InventoryStatus[]>("/catalog/inventory/status");
        return response.data;
    },

    async listLocations(): Promise<InventoryLocation[]> {
        const response = await apiClient.get<InventoryLocation[]>("/catalog/locations");
        return response.data;
    },

    async updateInventory(sku: string, location_code: string, new_qty: number): Promise<void> {
        await apiClient.post("/catalog/inventory/update", { sku, location_code, new_qty });
    },

    // Generic Offering Catalog
    async listOfferings(): Promise<TenantOffering[]> {
        const response = await apiClient.get<TenantOffering[]>("/catalog/offerings");
        return response.data;
    },

    async getOffering(offeringId: string): Promise<TenantOffering> {
        const response = await apiClient.get<TenantOffering>(`/catalog/offerings/${offeringId}`);
        return response.data;
    },

    async createOffering(data: { code: string; name: string; bot_id?: string; domain_id?: string; description?: string; status?: string }): Promise<TenantOffering> {
        const response = await apiClient.post<TenantOffering>("/catalog/offerings", data);
        return response.data;
    },

    async updateOffering(offeringId: string, data: Partial<TenantOffering>): Promise<TenantOffering> {
        const response = await apiClient.put<TenantOffering>(`/catalog/offerings/${offeringId}`, data);
        return response.data;
    },

    async deleteOffering(offeringId: string): Promise<{ message: string }> {
        const response = await apiClient.delete<{ message: string }>(`/catalog/offerings/${offeringId}`);
        return response.data;
    },

    // Offering Attributes (V4 linked to Version)
    async listOfferingAttributes(versionId: string): Promise<OfferingAttribute[]> {
        const response = await apiClient.get<OfferingAttribute[]>(`/catalog/versions/${versionId}/attributes`);
        return response.data;
    },

    async listDomainAttributes(domainId: string): Promise<any[]> {
        const response = await apiClient.get<any[]>(`/knowledge/attribute-definitions`, {
            params: { domain_id: domainId }
        });
        return response.data;
    },

    async createOfferingAttribute(versionId: string, data: { attribute_key: string; attribute_value: string; value_type?: string; display_order?: number }): Promise<OfferingAttribute> {
        const response = await apiClient.post<OfferingAttribute>(`/catalog/versions/${versionId}/attributes`, data);
        return response.data;
    },

    async updateOfferingAttribute(versionId: string, attributeId: string, data: Partial<OfferingAttribute>): Promise<OfferingAttribute> {
        const response = await apiClient.put<OfferingAttribute>(`/catalog/versions/${versionId}/attributes/${attributeId}`, data);
        return response.data;
    },

    async listPriceLists(): Promise<PriceList[]> {
        const response = await apiClient.get<PriceList[]>("/catalog/price-lists");
        return response.data;
    },

    async listChannels(): Promise<SalesChannel[]> {
        const response = await apiClient.get<SalesChannel[]>("/catalog/channels");
        return response.data;
    },

    // Channel Config (BotChannelConfig for Zalo, Facebook tokens)
    async listChannelConfigs(params: { bot_id?: string; bot_version_id?: string }): Promise<ChannelConfig[]> {
        const response = await apiClient.get<ChannelConfig[]>("/channel-configs", { params });
        return response.data;
    },
    async createOrUpdateChannelConfig(data: { bot_version_id: string; channel_code: string; config?: Record<string, unknown>; is_active?: boolean }): Promise<ChannelConfig> {
        const response = await apiClient.post<ChannelConfig>("/channel-configs", data);
        return response.data;
    },
    async updateChannelConfig(id: string, data: { config?: Record<string, unknown>; is_active?: boolean }): Promise<ChannelConfig> {
        const response = await apiClient.put<ChannelConfig>(`/channel-configs/${id}`, data);
        return response.data;
    },
    async deleteChannelConfig(id: string): Promise<{ message: string }> {
        const response = await apiClient.delete<{ message: string }>(`/channel-configs/${id}`);
        return response.data;
    },

    async deleteOfferingAttribute(versionId: string, attributeId: string): Promise<{ message: string }> {
        const response = await apiClient.delete<{ message: string }>(`/catalog/versions/${versionId}/attributes/${attributeId}`);
        return response.data;
    },

    // Variant & Price Management
    async createVariant(offeringId: string, data: { sku: string; name: string }): Promise<OfferingVariant> {
        const response = await apiClient.post<OfferingVariant>(`/catalog/offerings/${offeringId}/variants`, data);
        return response.data;
    },

    async updateVariant(variantId: string, data: { name?: string; status?: string }): Promise<OfferingVariant> {
        const response = await apiClient.put<OfferingVariant>(`/catalog/variants/${variantId}`, data);
        return response.data;
    },

    async deleteVariant(variantId: string): Promise<{ message: string }> {
        const response = await apiClient.delete<{ message: string }>(`/catalog/variants/${variantId}`);
        return response.data;
    },

    async setVariantPrice(variantId: string, data: { price_list_id: string; amount: number; currency?: string; price_type?: string; compare_at?: number }): Promise<VariantPrice> {
        const response = await apiClient.post<VariantPrice>(`/catalog/variants/${variantId}/prices`, data);
        return response.data;
    },

    // Domain Management
    async listDomains(): Promise<KnowledgeDomain[]> {
        const response = await apiClient.get<KnowledgeDomain[]>("/knowledge/domains");
        return response.data;
    },

    async listAttributeDefinitions(domainId?: string): Promise<DomainAttributeDefinition[]> {
        const response = await apiClient.get<DomainAttributeDefinition[]>("/knowledge/attribute-definitions", {
            params: { domain_id: domainId }
        });
        return response.data;
    },

    // Training & AI
    async listFAQs(domain_id?: string): Promise<FAQ[]> {
        const response = await apiClient.get<FAQ[]>("/faqs", { params: { domain_id } });
        return response.data;
    },

    async createFAQ(data: Partial<FAQ>): Promise<FAQ> {
        const response = await apiClient.post<FAQ>("/faqs", data);
        return response.data;
    },

    async updateFAQ(id: string, data: Partial<FAQ>): Promise<FAQ> {
        const response = await apiClient.put<FAQ>(`/faqs/${id}`, data);
        return response.data;
    },

    async deleteFAQ(id: string): Promise<{ message: string }> {
        const response = await apiClient.delete<{ message: string }>(`/faqs/${id}`);
        return response.data;
    },

    async listUseCases(offering_id?: string, domain_id?: string): Promise<UseCase[]> {
        const response = await apiClient.get<UseCase[]>("/usecases", { params: { offering_id, domain_id } });
        return response.data;
    },

    async createUseCase(data: Partial<UseCase>): Promise<UseCase> {
        const response = await apiClient.post<UseCase>("/usecases", data);
        return response.data;
    },

    async updateUseCase(id: string, data: Partial<UseCase>): Promise<UseCase> {
        const response = await apiClient.put<UseCase>(`/usecases/${id}`, data);
        return response.data;
    },

    async deleteUseCase(id: string): Promise<{ message: string }> {
        const response = await apiClient.delete<{ message: string }>(`/usecases/${id}`);
        return response.data;
    },

    async listComparisons(domain_id?: string): Promise<Comparison[]> {
        const response = await apiClient.get<Comparison[]>("/comparisons", { params: { domain_id } });
        return response.data;
    },

    async createComparison(data: Partial<Comparison>): Promise<Comparison> {
        const response = await apiClient.post<Comparison>("/comparisons", data);
        return response.data;
    },

    async updateComparison(id: string, data: Partial<Comparison>): Promise<Comparison> {
        const response = await apiClient.put<Comparison>(`/comparisons/${id}`, data);
        return response.data;
    },

    async deleteComparison(id: string): Promise<{ message: string }> {
        const response = await apiClient.delete<{ message: string }>(`/comparisons/${id}`);
        return response.data;
    },

    async listGuardrails(active_only?: boolean): Promise<Guardrail[]> {
        const response = await apiClient.get<Guardrail[]>("/guardrails", { params: { active_only } });
        return response.data;
    },

    async createGuardrail(data: Partial<Guardrail>): Promise<Guardrail> {
        const response = await apiClient.post<Guardrail>("/guardrails", data);
        return response.data;
    },

    async updateGuardrail(id: string, data: Partial<Guardrail>): Promise<Guardrail> {
        const response = await apiClient.put<Guardrail>(`/guardrails/${id}`, data);
        return response.data;
    },

    async deleteGuardrail(id: string): Promise<{ message: string }> {
        const response = await apiClient.delete<{ message: string }>(`/guardrails/${id}`);
        return response.data;
    },

    async listCache(): Promise<any[]> {
        const response = await apiClient.get<any[]>("/cache");
        return response.data;
    },

    // Migration Hub
    async startScrape(data: { url: string; bot_id?: string; domain_id?: string }): Promise<{ job_id: string; status: string; message: string }> {
        const response = await apiClient.post("/catalog/migrate/scrape", data);
        return response.data;
    },

    async getMigrationJob(jobId: string): Promise<MigrationJob> {
        const response = await apiClient.get<MigrationJob>(`/catalog/migrate/jobs/${jobId}`);
        return response.data;
    },

    async confirmMigration(jobId: string): Promise<{ message: string }> {
        const response = await apiClient.post<{ message: string }>(`/catalog/migrate/jobs/${jobId}/confirm`);
        return response.data;
    },

    async listMigrationJobs(): Promise<MigrationJob[]> {
        const response = await apiClient.get<MigrationJob[]>("/catalog/migrate/jobs");
        return response.data;
    },

    async listContacts(params?: { skip?: number; limit?: number }): Promise<Contact[]> {
        const response = await apiClient.get<Contact[]>("/contacts", { params });
        return response.data;
    },

    async getAnalytics(days?: number): Promise<AnalyticsDashboard> {
        const response = await apiClient.get<AnalyticsDashboard>("/analytics/dashboard", { params: days ? { days } : {} });
        return response.data;
    },

    async getStateStatistics(): Promise<{ distribution: Record<string, number>; total_active: number; updated_at: string }> {
        const response = await apiClient.get("/analytics/state-statistics");
        return response.data;
    },
};
