import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Box,
  Flex,
  HStack,
  VStack,
  Text,
  Button,
  IconButton,
  Avatar,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  MenuDivider,
  useColorModeValue,
  useDisclosure,
  Drawer,
  DrawerOverlay,
  DrawerContent,
  DrawerHeader,
  DrawerBody,
  Icon,
} from '@chakra-ui/react';
import {
  FiMenu,
  FiX,
  FiHome,
  FiUpload,
  FiList,
  FiMessageSquare,
  FiSearch,
  FiSettings,
  FiLogOut,
  FiUser,
} from 'react-icons/fi';
import { useAuth } from '../../contexts/AuthContext';

const Navigation = ({ children }) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const { user, logout } = useAuth();
  const location = useLocation();
  
  const menuItems = [
    { name: 'Dashboard', path: '/', icon: FiHome },
    { name: 'Dokümanlar', path: '/documents', icon: FiList },
    { name: 'Doküman Yükle', path: '/upload', icon: FiUpload },
    { name: 'Sohbet', path: '/chat', icon: FiMessageSquare },
    { name: 'Bilgi Arama', path: '/query', icon: FiSearch },  // Add this item
    { name: 'Ayarlar', path: '/settings', icon: FiSettings },
  ];
  
  const handleLogout = () => {
    logout();
  };
  
  return (
    <Box minH="100vh" bg={useColorModeValue('gray.50', 'gray.900')}>
      {/* Mobile nav header */}
      <Flex
        bg={useColorModeValue('white', 'gray.800')}
        color={useColorModeValue('gray.600', 'white')}
        minH="60px"
        py={{ base: 2 }}
        px={{ base: 4 }}
        borderBottom={1}
        borderStyle="solid"
        borderColor={useColorModeValue('gray.200', 'gray.700')}
        align="center"
        display={{ base: 'flex', md: 'none' }}
      >
        <IconButton
          icon={isOpen ? <FiX /> : <FiMenu />}
          variant="ghost"
          onClick={isOpen ? onClose : onOpen}
          aria-label="Toggle Navigation"
        />
        
        <Flex flex={{ base: 1 }} justify="center">
          <Text
            fontSize="xl"
            fontWeight="bold"
            color="brand.600"
          >
            RAG System
          </Text>
        </Flex>
        
        <Menu>
          <MenuButton
            as={Button}
            rounded="full"
            variant="link"
            cursor="pointer"
            minW={0}
          >
            <Avatar
              size="sm"
              name={user?.name || user?.email}
            />
          </MenuButton>
          <MenuList>
            <MenuItem icon={<FiUser />}>Profil</MenuItem>
            <MenuItem icon={<FiSettings />}>Ayarlar</MenuItem>
            <MenuDivider />
            <MenuItem icon={<FiLogOut />} onClick={handleLogout}>Çıkış Yap</MenuItem>
          </MenuList>
        </Menu>
      </Flex>
      
      {/* Mobile Drawer */}
      <Drawer
        isOpen={isOpen}
        placement="left"
        onClose={onClose}
        size="xs"
      >
        <DrawerOverlay />
        <DrawerContent>
          <DrawerHeader borderBottomWidth="1px">
            <Flex align="center">
              <Text fontSize="xl" fontWeight="bold" color="brand.600">
                RAG System
              </Text>
            </Flex>
          </DrawerHeader>
          <DrawerBody p={0}>
            <VStack spacing={0} align="stretch">
              {menuItems.map((item) => (
                <Link to={item.path} key={item.path} onClick={onClose}>
                  <Flex
                    py={3}
                    px={4}
                    align="center"
                    fontWeight="medium"
                    bg={location.pathname === item.path ? 'brand.50' : 'transparent'}
                    color={location.pathname === item.path ? 'brand.600' : 'gray.700'}
                    borderLeftWidth={location.pathname === item.path ? '4px' : '0px'}
                    borderColor="brand.500"
                    _hover={{
                      bg: 'gray.100',
                    }}
                  >
                    <Icon as={item.icon} mr={3} />
                    {item.name}
                  </Flex>
                </Link>
              ))}
            </VStack>
          </DrawerBody>
        </DrawerContent>
      </Drawer>
      
      {/* Desktop sidebar */}
      <Flex display={{ base: 'none', md: 'flex' }}>
        <Box
          w="240px"
          h="100vh"
          position="fixed"
          borderRight="1px"
          borderColor={useColorModeValue('gray.200', 'gray.700')}
          bg={useColorModeValue('white', 'gray.800')}
        >
          <Flex
            h="20"
            alignItems="center"
            mx="8"
            justifyContent="space-between"
          >
            <Text
              fontSize="2xl"
              fontWeight="bold"
              color="brand.600"
            >
              RAG System
            </Text>
          </Flex>
          
          <VStack spacing={0} align="stretch" mt={6}>
            {menuItems.map((item) => (
              <Link to={item.path} key={item.path}>
                <Flex
                  py={3}
                  px={8}
                  align="center"
                  fontWeight="medium"
                  bg={location.pathname === item.path ? 'brand.50' : 'transparent'}
                  color={location.pathname === item.path ? 'brand.600' : 'gray.700'}
                  borderLeftWidth={location.pathname === item.path ? '4px' : '0px'}
                  borderColor="brand.500"
                  _hover={{
                    bg: 'gray.100',
                  }}
                >
                  <Icon as={item.icon} mr={3} />
                  {item.name}
                </Flex>
              </Link>
            ))}
          </VStack>
          
          <Flex
            position="absolute"
            bottom="0"
            w="full"
            p={4}
            borderTop="1px"
            borderColor={useColorModeValue('gray.200', 'gray.700')}
          >
            <Menu>
              <MenuButton
                as={Button}
                variant="ghost"
                size="sm"
                w="full"
                leftIcon={<Avatar size="xs" name={user?.name || user?.email} />}
                justifyContent="flex-start"
                fontWeight="normal"
              >
                <Flex direction="column" alignItems="flex-start">
                  <Text fontSize="sm" fontWeight="medium">
                    {user?.name || user?.email}
                  </Text>
                </Flex>
              </MenuButton>
              <MenuList>
                <MenuItem icon={<FiUser />}>Profil</MenuItem>
                <MenuItem icon={<FiSettings />}>Ayarlar</MenuItem>
                <MenuDivider />
                <MenuItem icon={<FiLogOut />} onClick={handleLogout}>Çıkış Yap</MenuItem>
              </MenuList>
            </Menu>
          </Flex>
        </Box>
        
        {/* Main content */}
        <Box ml={{ base: 0, md: '240px' }} w="100%">
          {children}
        </Box>
      </Flex>
      
      {/* Mobile content (without sidebar offset) */}
      <Box
        display={{ base: 'block', md: 'none' }}
        pt="60px"
      >
        {children}
      </Box>
    </Box>
  );
};

export default Navigation;