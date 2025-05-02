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
  Checkbox,
  Flex,
  Divider,
  Card,
  CardBody,
} from '@chakra-ui/react';
import { FiEye, FiEyeOff, FiLogIn } from 'react-icons/fi';
import { useAuth } from '../../contexts/AuthContext';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [rememberMe, setRememberMe] = useState(false);
  
  const navigate = useNavigate();
  const toast = useToast();
  const { login } = useAuth();

  const validateForm = () => {
    const newErrors = {};
    
    if (!email) {
      newErrors.email = 'E-posta gereklidir';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = 'Geçerli bir e-posta adresi giriniz';
    }
    
    if (!password) {
      newErrors.password = 'Şifre gereklidir';
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
      await login(email, password, rememberMe);
      
      toast({
        title: 'Giriş başarılı',
        description: 'Hoş geldiniz!',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      
      // Redirect to dashboard
      navigate('/');
    } catch (error) {
      toast({
        title: 'Giriş hatası',
        description: error.message || 'Giriş yapılamadı',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
      
      setErrors({
        auth: error.message || 'Geçersiz e-posta veya şifre'
      });
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
              <Heading size="lg" mb={2}>RAG Sistemi Giriş</Heading>
              <Text color="gray.600">Hesabınıza giriş yapın</Text>
            </Box>
            
            {errors.auth && (
              <Box p={3} bg="red.50" borderRadius="md" borderWidth="1px" borderColor="red.300">
                <Text color="red.500">{errors.auth}</Text>
              </Box>
            )}
            
            <form onSubmit={handleSubmit}>
              <VStack spacing={4}>
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
                
                <Flex justify="space-between" w="full" align="center">
                  <Checkbox
                    isChecked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                  >
                    Beni hatırla
                  </Checkbox>
                  
                  <Link to="/forgot-password">
                    <Text color="brand.600" fontSize="sm" fontWeight="medium">
                      Şifremi unuttum
                    </Text>
                  </Link>
                </Flex>
                
                <Button
                  type="submit"
                  colorScheme="brand"
                  size="lg"
                  width="full"
                  mt={4}
                  isLoading={isLoading}
                  leftIcon={<FiLogIn />}
                >
                  Giriş Yap
                </Button>
              </VStack>
            </form>
            
            <Divider />
            
            <Text textAlign="center">
              Hesabınız yok mu?{' '}
              <Link to="/register">
                <Text as="span" color="brand.600" fontWeight="semibold">
                  Kayıt olun
                </Text>
              </Link>
            </Text>
          </VStack>
        </CardBody>
      </Card>
    </Box>
  );
};

export default Login;