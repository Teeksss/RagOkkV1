import DOMPurify from 'dompurify';

/**
 * HTML içeriğini sanitize eder
 * 
 * @param {string} html Sanitize edilecek HTML
 * @returns {string} Sanitize edilmiş HTML
 */
export const sanitizeHtml = (html) => {
  if (!html) return '';
  
  // DOMPurify ile HTML'i temizle
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'hr',
      'ul', 'ol', 'li', 'blockquote', 'pre', 'code',
      'em', 'strong', 'del', 'a', 'img', 'table', 'thead',
      'tbody', 'tr', 'th', 'td', 'span'
    ],
    ALLOWED_ATTR: [
      'href', 'src', 'alt', 'title', 'class', 'target',
      'rel', 'id', 'style'
    ],
    FORBID_TAGS: ['script', 'style', 'iframe', 'frame', 'object', 'embed'],
    ADD_ATTR: ['target'], // target="_blank" için
    FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover'],
    ALLOW_ARIA_ATTR: true,
    USE_PROFILES: { html: true },
    SANITIZE_DOM: true
  });
};

/**
 * Metin girişlerini sanitize eder
 * 
 * @param {string} text Sanitize edilecek metin
 * @returns {string} Sanitize edilmiş metin
 */
export const sanitizeText = (text) => {
  if (!text) return '';
  
  // HTML karakterlerini escape et
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
};

/**
 * URL'leri sanitize eder
 * 
 * @param {string} url Sanitize edilecek URL
 * @returns {string|null} Sanitize edilmiş URL veya null
 */
export const sanitizeUrl = (url) => {
  if (!url) return null;
  
  // URL formatını kontrol et
  try {
    const parsed = new URL(url);
    
    // Sadece güvenli protokollere izin ver
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
      return null;
    }
    
    return parsed.toString();
  } catch (error) {
    return null;
  }
};

/**
 * Dosya adlarını sanitize eder
 * 
 * @param {string} filename Sanitize edilecek dosya adı
 * @returns {string} Sanitize edilmiş dosya adı
 */
export const sanitizeFilename = (filename) => {
  if (!filename) return '';
  
  // Tehlikeli karakterleri temizle
  return filename
    .replace(/[/\\?%*:|"<>]/g, '-') // Yasaklı dosya adı karakterleri
    .replace(/\.\./g, '-') // Path traversal önleme
    .replace(/\s+/g, '_'); // Boşlukları alt çizgi ile değiştir
};

/**
 * Arama sorgusunu sanitize eder
 * 
 * @param {string} query Sanitize edilecek arama sorgusu
 * @returns {string} Sanitize edilmiş arama sorgusu
 */
export const sanitizeSearchQuery = (query) => {
  if (!query) return '';
  
  // SQL injection önlemleri
  return query
    .replace(/[;'"\\]/g, '') // Tehlikeli karakterleri kaldır
    .trim();
};