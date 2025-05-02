import { useState, useEffect } from 'react';

/**
 * Local storage entegrasyonu için özelleştirilmiş hook
 * 
 * @param {string} key Storage anahtarı
 * @param {any} initialValue Başlangıç değeri
 * @returns {Array} Değer ve setter fonksiyonu
 */
export const useLocalStorage = (key, initialValue) => {
  // Getter fonksiyonu - localStorage'dan değeri alır veya ilk değeri kullanır
  const readValue = () => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  };

  // Değeri state olarak sakla
  const [storedValue, setStoredValue] = useState(readValue);

  // Setter fonksiyonu - değeri hem state'te hem localStorage'da günceller
  const setValue = value => {
    try {
      // Fonksiyon olarak değer atama desteği
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      
      // State'i güncelle
      setStoredValue(valueToStore);
      
      // localStorage'a kaydet
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
      
      // Storage değişiklik olayı yayınla
      window.dispatchEvent(new Event('local-storage'));
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error);
    }
  };

  // Başka sekme/pencereden localStorage değişikliklerini dinle
  useEffect(() => {
    const handleStorageChange = () => {
      setStoredValue(readValue());
    };
    
    // Olay dinleyicilerini ekle
    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('local-storage', handleStorageChange);
    
    // Temizleme
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('local-storage', handleStorageChange);
    };
  }, [key, readValue]);

  return [storedValue, setValue];
};