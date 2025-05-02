// Token güvenlik fonksiyonları eklenmeli

/**
 * JWT token'ının güvenliğini kontrol eder
 * 
 * @param {string} token JWT token
 * @returns {boolean} Token'ın güvenli olup olmadığı
 */
export const validateTokenSecurity = (token) => {
  try {
    // Token'ın parçalarını ayır
    const parts = token.split('.');
    
    if (parts.length !== 3) {
      console.warn('Invalid JWT format');
      return false;
    }
    
    // Payload'ı decode et
    const payload = JSON.parse(atob(parts[1]));
    
    // Kritik güvenlik kontrollerini yap
    
    // 1. Token'ın süresinin geçip geçmediğini kontrol et
    const now = Math.floor(Date.now() / 1000);
    if (!payload.exp || payload.exp <= now) {
      console.warn('Token expired');
      return false;
    }
    
    // 2. Token'ın henüz geçerli olup olmadığını kontrol et (iat/nbf)
    if (payload.nbf && payload.nbf > now) {
      console.warn('Token not yet valid');
      return false;
    }
    
    // 3. Beklenen audience'ı kontrol et
    const expectedAudience = process.env.REACT_APP_JWT_AUDIENCE || 'rag-app';
    if (payload.aud && payload.aud !== expectedAudience) {
      console.warn('Token audience mismatch');
      return false;
    }
    
    // 4. Beklenen issuer'ı kontrol et
    const expectedIssuer = process.env.REACT_APP_JWT_ISSUER || 'rag-api';
    if (payload.iss && payload.iss !== expectedIssuer) {
      console.warn('Token issuer mismatch');
      return false;
    }
    
    return true;
  } catch (error) {
    console.error('Token validation error:', error);
    return false;
  }
};

/**
 * Oturum açma sırasında yeni alınan token'ları güvenlik açısından kontrol eder
 * 
 * @param {Object} authResponse Auth API yanıtı
 * @returns {boolean} Token'ların güvenli olup olmadığı
 */
export const validateAuthTokens = (authResponse) => {
  // Access token'ı kontrol et
  if (!validateTokenSecurity(authResponse.access_token)) {
    return false;
  }
  
  // Refresh token varsa kontrol et
  if (authResponse.refresh_token && !validateTokenSecurity(authResponse.refresh_token)) {
    return false;
  }
  
  return true;
};