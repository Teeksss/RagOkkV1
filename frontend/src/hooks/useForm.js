import { useState, useCallback } from 'react';

/**
 * Form state ve validasyon için özelleştirilmiş hook
 * 
 * @param {Object} initialValues Form başlangıç değerleri
 * @param {Function} validate Doğrulama fonksiyonu
 * @returns {Object} Form handlers ve state
 */
export const useForm = (initialValues = {}, validate = () => ({})) => {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Input değişikliklerini yönet
  const handleChange = useCallback((e) => {
    const { name, value, type, checked } = e.target;
    const inputValue = type === 'checkbox' ? checked : value;
    
    setValues(prev => ({
      ...prev,
      [name]: inputValue
    }));
    
    // Dokunulan alanları izle
    if (!touched[name]) {
      setTouched(prev => ({
        ...prev,
        [name]: true
      }));
    }
  }, [touched]);

  // Blur olaylarını yönet
  const handleBlur = useCallback((e) => {
    const { name } = e.target;
    
    setTouched(prev => ({
      ...prev,
      [name]: true
    }));
    
    // Dokunulan alanları doğrula
    const validationErrors = validate(values);
    setErrors(validationErrors);
  }, [values, validate]);

  // Form gönderimini yönet
  const handleSubmit = useCallback((onSubmit) => async (e) => {
    e.preventDefault();
    
    // Tüm alanlara dokunulmuş olarak işaretle
    const allTouched = Object.keys(values).reduce((acc, key) => {
      acc[key] = true;
      return acc;
    }, {});
    setTouched(allTouched);
    
    // Doğrulama hatalarını kontrol et
    const validationErrors = validate(values);
    setErrors(validationErrors);
    
    // Hata yoksa gönderimi işle
    if (Object.keys(validationErrors).length === 0) {
      setIsSubmitting(true);
      try {
        await onSubmit(values);
      } catch (error) {
        console.error('Form submission error:', error);
      } finally {
        setIsSubmitting(false);
      }
    }
  }, [values, validate]);

  // Form sıfırlama
  const reset = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
    setIsSubmitting(false);
  }, [initialValues]);

  return {
    values,
    errors,
    touched,
    isSubmitting,
    handleChange,
    handleBlur,
    handleSubmit,
    reset,
    setValues
  };
};