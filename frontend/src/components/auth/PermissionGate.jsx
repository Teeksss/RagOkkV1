import React from 'react';
import PropTypes from 'prop-types';
import { useContext } from 'react';
import { AuthContext } from '../../contexts/AuthContext';

/**
 * Yetkilendirme kontrolü yaparak içeriği şartlı render eden bileşen
 * 
 * @param {Object} props Bileşen props'ları
 * @param {Array<string>} props.permissions İzin verilen yetkiler dizisi
 * @param {Array<string>} props.roles İzin verilen roller dizisi
 * @param {boolean} props.requireAllPermissions Tüm yetkilerin gerekli olup olmadığı
 * @param {React.ReactNode} props.children Yetkili içerik
 * @param {React.ReactNode} props.fallback Yetkisiz durumda gösterilecek içerik
 * @returns {JSX.Element|null} Render edilen içerik
 */
const PermissionGate = ({
  permissions = [],
  roles = [],
  requireAllPermissions = false,
  children,
  fallback = null
}) => {
  const { user, isAuthenticated } = useContext(AuthContext);
  
  if (!isAuthenticated || !user) {
    return fallback;
  }
  
  // Rol kontrolü
  if (roles.length > 0) {
    const userRole = user.role || (user.is_admin ? 'admin' : 'user');
    const hasRequiredRole = roles.includes(userRole);
    
    if (!hasRequiredRole) {
      return fallback;
    }
  }
  
  // İzin kontrolü
  if (permissions.length > 0 && user.permissions) {
    if (requireAllPermissions) {
      // Tüm izinlerin olması gerekiyor
      const hasAllPermissions = permissions.every(permission => 
        user.permissions.includes(permission)
      );
      
      if (!hasAllPermissions) {
        return fallback;
      }
    } else {
      // En az bir izin olması yeterli
      const hasAnyPermission = permissions.some(permission => 
        user.permissions.includes(permission)
      );
      
      if (!hasAnyPermission) {
        return fallback;
      }
    }
  }
  
  // Kullanıcı admin ise her zaman erişim ver
  if (user.is_admin) {
    return children;
  }
  
  return children;
};

PermissionGate.propTypes = {
  permissions: PropTypes.arrayOf(PropTypes.string),
  roles: PropTypes.arrayOf(PropTypes.string),
  requireAllPermissions: PropTypes.bool,
  children: PropTypes.node.isRequired,
  fallback: PropTypes.node
};

export default PermissionGate;