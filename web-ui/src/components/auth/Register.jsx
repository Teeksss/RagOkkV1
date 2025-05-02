import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  InputGroup,
  InputRightElement,
  FormErrorMessage,
  Heading,
  Text,
  VStack,
  useToast,
  Icon,
  Divider,
  Card,
  CardBody,
  Alert,
  AlertIcon,
} from '@chakra-ui/react';
import { FiEye, FiEyeOff, FiUserPlus } from 'react-icons/fi';
import { useAuth } from '../../contexts/AuthContext';

const Register = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState({});
  
  const navigate = useNavigate();
  const toast = useToast();
  const { register } = useAuth();

  const validateForm = () => {
    const newErrors = {};
    
    if (!name) {
      newErrors.name = 'İsim gereklidir';
    }
    
    if (!email) {
      newErrors.email = 'E-posta gereklidir';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = 'Geçerli bir e-posta adresi giriniz';
    }
    
    if (!password) {
      newErrors.password = 'Şifre gereklidir';
    } else if (password.length < 8) {
      newErrors.password = 'Şifre en az 8 karakter olmalıdır';
    } else if (!/[A-Z]/.test(password)) {
      newErrors.password = 'Şifre en az bir büyük harf içermelidir';
    } else if (!/[a-z]/.test(password)) {
      newErrors.password = 'Şifre en az bir küçük harf içermelidir';
    } else if (!/[0-9]/.test(password)) {
      newErrors.password = 'Şifre en az bir rakam içermelidir';
    }
    
    if (!passwordConfirm) {
      newErrors.passwordConfirm = 'Şifre tekrarı gereklidir';
    } else if (password !== passwordConfirm) {
      newErrors.passwordConfirm = 'Şifreler eşleşmiyor';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsLoading(true);
    
    try {
      await register(name, email, password, passwordConfirm);
      
      toast({
        title: 'Kayıt başarılı',
        description: 'Hesabınız oluşturuldu. Giriş yapabilirsiniz.',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
      
      navigate('/login');
    } catch (error) {
      toast({
        title: 'Kayıt hatası',
        description: error.message || 'Kayıt yapılamadı',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
      
      if (error.response?.data?.detail === 'Bu e-posta adresi zaten kullanılıyor') {
        setErrors({
          email: 'Bu e-posta adresi zaten kullanılıyor'
        });
      } else {
        setErrors({
          form: error.message || 'Kayıt işlemi sırasında bir hata oluştu'
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box minH="100vh" display="flex" alignItems="center" justifyContent="center" bg="gray.50">
      <Card maxW="md" w="full" boxShadow="lg" borderRadius="xl">
        <CardBody p={8}>
          <VStack spacing={6} align="stretch">
            <Box textAlign="center">
              <Heading size="lg" mb={2}>RAG Sistemi Kayıt</Heading>
              <Text color="gray.600">Yeni bir hesap oluşturun</Text>
            </Box>
            
            {errors.form && (
              <Alert status="error" borderRadius="md">
                <AlertIcon />
                {errors.form}
              </Alert>
            )}
            
            <form onSubmit={handleSubmit}>
              <VStack spacing={4}>
                <FormControl isInvalid={errors.name}>
                  <FormLabel>Ad Soyad</FormLabel>
                  <Input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Ad Soyad"
                    size="lg"
                  />
                  <FormErrorMessage>{errors.name}</FormErrorMessage>
                </FormControl>
                
                <FormControl isInvalid={errors.email}>
                  <FormLabel>E-posta</FormLabel>
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="eposta@example.com"
                    size="lg"
                  />
                  <FormErrorMessage>{errors.email}</FormErrorMessage>
                </FormControl>
                
                <FormControl isInvalid={errors.password}>
                  <FormLabel>Şifre</FormLabel>
                  <InputGroup>
                    <Input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="********"
                      size="lg"
                    />
                    <InputRightElement h="full">
                      <Button
                        variant="ghost"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        <Icon as={showPassword ? FiEyeOff : FiEye} />
                      </Button>
                    </InputRightElement>
                  </InputGroup>
                  <FormErrorMessage>{errors.password}</FormErrorMessage>
                </FormControl>
                
                <FormControl isInvalid={errors.passwordConfirm}>
                  <FormLabel>Şifre Tekrarı</FormLabel>
                  <InputGroup>
                    <Input
                      type={showPassword ? 'text' : 'password'}
                      value={passwordConfirm}
                      onChange={(e) => setPasswordConfirm(e.target.value)}
                      placeholder="********"
                      size="lg"
                    />
                    <InputRightElement h="full">
                      <Button
                        variant="ghost"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        <Icon as={showPassword ? FiEyeOff : FiEye} />
                      </Button>
                    </InputRightElement>
                  </InputGroup>
                  <FormErrorMessage>{errors.passwordConfirm}</FormErrorMessage>
                </FormControl>
                
                <Button
                  type="submit"
                  colorScheme="brand"
                  size="lg"
                  width="full"
                  mt={4}
                  isLoading={isLoading}
                  leftIcon={<FiUserPlus />}
                >
                  Kayıt Ol
                </Button>
              </VStack>
            </form>
            
            <Divider />
            
            <Text textAlign="center">
              Zaten hesabınız var mı?{' '}
              <Link to="/login">
                <Text as="span" color="brand.600" fontWeight="semibold">
                  Giriş yapın
                </Text>
              </Link>
            </Text>
          </VStack>
        </CardBody>
      </Card>
    </Box>
  );
};

export default Register;