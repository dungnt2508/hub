/**
 * Secure Auth Routes
 * 
 * RULE: Catalog Auth Service is the SINGLE trust anchor
 * RULE: These endpoints implement the secure authentication architecture
 */

import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import googleAuthService from '../services/google-auth.service';
import internalJWTService from '../services/internal-jwt.service';
import refreshTokenService from '../services/refresh-token.service';
import jwtKeyService from '../services/jwt-key.service';
import userRepository from '../repositories/user.repository';
import authProviderRepository from '../repositories/auth-provider.repository';
import { successResponse, errorResponse, unauthorizedResponse } from '../utils/response';
import { UserMapper } from '../application/mappers/user.mapper';
import { UserRole } from '@gsnake/shared-types';
import { z } from 'zod';

// Request schemas
const googleAuthSchema = z.object({
    id_token: z.string().min(1, 'id_token is required'),
    audience: z.string().default('bot-service'),  // Target service audience
});

const refreshTokenSchema = z.object({
    refresh_token: z.string().min(1, 'refresh_token is required'),
    audience: z.string().default('bot-service'),  // Target service audience
});

const logoutSchema = z.object({
    refresh_token: z.string().min(1, 'refresh_token is required'),
});

export default async function secureAuthRoutes(fastify: FastifyInstance) {
    // Debug: Log route registration
    fastify.log.info('🔐 Registering secure auth routes...');
    
    /**
     * POST /api/auth/google
     * 
     * RULE: Google OAuth is used ONLY for initial identity verification
     * RULE: Verify Google id_token
     * RULE: Do NOT propagate Google tokens downstream
     * RULE: Issue internal access_token + refresh_token
     * 
     * Note: This is POST, while GET /api/auth/google is in auth.routes.ts
     */
    fastify.post('/google', async (request: FastifyRequest, reply: FastifyReply) => {
        fastify.log.info('POST /api/auth/google called');
        try {
            // Validate request body
            const body = googleAuthSchema.parse(request.body);
            const { id_token, audience } = body;

            // RULE: Verify Google id_token with Google public keys
            const googlePayload = await googleAuthService.verifyIdToken(id_token);

            // Map or create internal user
            let user = await authProviderRepository
                .findByProviderUser('google', googlePayload.sub)
                .then(record => record ? userRepository.findById(record.user_id) : null)
                .then(user => user ? Promise.resolve(user) : null);

            // Fallback to email lookup
            if (!user) {
                user = await userRepository.findByEmail(googlePayload.email);
            }

            // Create user if not exists
            if (!user) {
                user = await userRepository.create({
                    email: googlePayload.email,
                    role: UserRole.USER,
                });
            }

            // Ensure auth_provider record exists (NO tokens stored)
            await authProviderRepository.upsert({
                user_id: user.id,
                provider: 'google',
                provider_user_id: googlePayload.sub,
            });

            // RULE: Issue internal access_token + refresh_token
            const accessToken = await internalJWTService.generateAccessToken(
                user.id,
                user.role,
                audience
            );

            const { token: refreshToken, expiresAt } = await refreshTokenService.createToken(
                user.id,
                {
                    deviceInfo: request.headers['user-agent'] ? { userAgent: request.headers['user-agent'] } : undefined,
                    ipAddress: request.ip,
                }
            );

            const userDto = UserMapper.toResponseDto(user);

            return successResponse(reply, {
                user: userDto,
                access_token: accessToken,
                refresh_token: refreshToken,
                token_type: 'Bearer',
                expires_in: 30 * 60,  // 30 minutes in seconds
            }, 'Google authentication successful');
        } catch (error) {
            if (error instanceof z.ZodError) {
                return errorResponse(reply, 'Invalid request', 400, error.errors);
            }
            
            const message = error instanceof Error ? error.message : 'Google authentication failed';
            return unauthorizedResponse(reply, message);
        }
    });

    /**
     * POST /api/auth/refresh
     * 
     * RULE: Validate refresh token
     * RULE: Rotate refresh token
     * RULE: Issue new access_token
     */
    fastify.post('/refresh', async (request: FastifyRequest, reply: FastifyReply) => {
        fastify.log.info('POST /api/auth/refresh called');
        try {
            // Validate request body
            const body = refreshTokenSchema.parse(request.body);
            const { refresh_token, audience } = body;

            // RULE: Validate and rotate refresh token
            const { userId, newToken, newExpiresAt } = await refreshTokenService.validateAndRotateToken(refresh_token);

            // Get user
            const user = await userRepository.findById(userId);
            if (!user) {
                return unauthorizedResponse(reply, 'User not found');
            }

            // RULE: Issue new access_token
            const accessToken = await internalJWTService.generateAccessToken(
                user.id,
                user.role,
                audience
            );

            // Calculate expires_in
            const expiresIn = Math.floor((newExpiresAt.getTime() - Date.now()) / 1000);

            return successResponse(reply, {
                access_token: accessToken,
                refresh_token: newToken,
                token_type: 'Bearer',
                expires_in: 30 * 60,  // 30 minutes in seconds
            }, 'Token refreshed successfully');
        } catch (error) {
            if (error instanceof z.ZodError) {
                return errorResponse(reply, 'Invalid request', 400, error.errors);
            }

            const message = error instanceof Error ? error.message : 'Token refresh failed';
            return unauthorizedResponse(reply, message);
        }
    });

    /**
     * POST /api/auth/logout
     * 
     * RULE: Logout revokes refresh token
     * RULE: Access tokens are NOT actively revoked (expire naturally)
     */
    fastify.post('/logout', async (request: FastifyRequest, reply: FastifyReply) => {
        try {
            // Validate request body
            const body = logoutSchema.parse(request.body);
            const { refresh_token } = body;

            // RULE: Revoke refresh token
            await refreshTokenService.revokeToken(refresh_token, 'logout');

            return successResponse(reply, {}, 'Logout successful');
        } catch (error) {
            if (error instanceof z.ZodError) {
                return errorResponse(reply, 'Invalid request', 400, error.errors);
            }

            // Don't reveal if token was invalid - always return success
            return successResponse(reply, {}, 'Logout successful');
        }
    });

    // Note: JWKS endpoint is registered separately in index.ts without /api prefix
}

