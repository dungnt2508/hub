import { FastifyRequest, FastifyReply } from 'fastify';
import userRepository from '../repositories/user.repository';
import { UserRole, SellerStatus } from '@gsnake/shared-types';
import { unauthorizedResponse } from '../utils/response';
import { AuthenticationError, AuthorizationError, ERROR_CODES } from '../shared/errors';
import jwt from 'jsonwebtoken';
import { createPublicKey } from 'crypto';
import jwtKeyService from '../services/jwt-key.service';

/**
 * Authenticate JWT token (used as preHandler)
 * 
 * RULE: Verify token với RS256 và JWKS (secure auth tokens)
 * RULE: Fallback to legacy HS256 verification for backward compatibility
 */
export async function authenticate(request: FastifyRequest, reply: FastifyReply) {
    try {
        // Extract token from Authorization header
        const authHeader = request.headers.authorization;
        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return unauthorizedResponse(reply, 'Missing or invalid authorization header');
        }

        const token = authHeader.substring(7);

        // Try to verify with RS256 (secure auth tokens)
        try {
            // Get kid from token header
            const decoded = jwt.decode(token, { complete: true });
            if (!decoded || typeof decoded === 'string' || !decoded.header.kid) {
                throw new Error('Token missing kid in header');
            }

            const kid = decoded.header.kid;
            
            // Get public key from JWKS
            const key = await jwtKeyService.getKeyByKid(kid);
            if (!key || key.is_revoked) {
                throw new Error('Key not found or revoked');
            }

            // Verify token with public key
            const publicKey = createPublicKey(key.public_key_pem);
            const payload = jwt.verify(token, publicKey, {
                algorithms: ['RS256'],
                issuer: 'catalog-auth',
                // Note: audience is optional - catalog service accepts tokens for any audience
                // Other services (like bot-service) will verify audience strictly
            }) as any;

            // Set user context
            // Note: email is not in token payload, will be fetched from DB if needed
            request.user = {
                userId: payload.sub,  // RULE: sub is internal user_id
                email: '',  // Will be populated from DB if needed
                role: payload.role as UserRole,
            };

            return; // Success
        } catch (rs256Error) {
            // If RS256 verification fails, try legacy HS256 (backward compatibility)
            try {
                await request.jwtVerify();
                return; // Success with legacy token
            } catch (hs256Error) {
                // Both failed
                request.log.debug({ rs256Error, hs256Error }, 'JWT verification failed');
                return unauthorizedResponse(reply, 'Invalid or expired token');
            }
        }
    } catch (err) {
        request.log.error({ err }, 'Authentication error');
        return unauthorizedResponse(reply, 'Invalid or expired token');
    }
}

/**
 * Require user to be authenticated
 */
export async function requireAuth(request: FastifyRequest, reply: FastifyReply) {
    if (!request.user) {
        return unauthorizedResponse(reply, 'Authentication required');
    }
}

/**
 * Require user to be admin
 * Checks role from JWT (no DB query needed)
 */
export async function requireAdmin(request: FastifyRequest, reply: FastifyReply) {
    if (!request.user) {
        return unauthorizedResponse(reply, 'Authentication required');
    }

    // Role is already in JWT payload, no need to query DB
    if (request.user.role !== UserRole.ADMIN) {
        return unauthorizedResponse(reply, 'Admin access required');
    }
}

/**
 * Require user to be approved seller
 * Checks role from JWT first, then queries DB only for seller_status
 */
export async function requireSeller(request: FastifyRequest, reply: FastifyReply) {
    if (!request.user) {
        return unauthorizedResponse(reply, 'Authentication required');
    }

    // Check role from JWT first (no DB query)
    if (request.user.role !== UserRole.SELLER) {
        return unauthorizedResponse(reply, 'Seller role required');
    }

    // Only query DB when we need to check seller_status (not in JWT)
    const user = await userRepository.findById(request.user.userId);
    if (!user || user.seller_status !== SellerStatus.APPROVED) {
        return unauthorizedResponse(reply, 'Approved seller access required. Please apply for seller status and wait for approval.');
    }
}
