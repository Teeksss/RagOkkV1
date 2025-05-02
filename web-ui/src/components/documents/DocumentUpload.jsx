import React, { useState, useRef } from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  VStack,
  Heading,
  Text,
  Progress,
  useToast,
  Alert,
  AlertIcon,
  Flex,
  Icon,
  Card,
  CardBody,
  HStack,
  Tag,
  Switch,
} from '@chakra-ui/react';
import { useDropzone } from 'react-dropzone';
import { FiUpload, FiFile, FiCheckCircle, FiTrash2, FiInfo } from 'react-icons/fi';
import { useApi } from '../../contexts/ApiContext';

const DocumentUpload = () => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [uploadSuccess, setUploadSuccess] = useState([]);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [enableOcr, setEnableOcr] = useState(true);
  const toast = useToast();
  const { api } = useApi();

  const onDrop = (acceptedFiles) => {
    const newFiles = acceptedFiles.map(file => ({
      file,
      id: Math.random().toString(36).substring(2, 15),
    }));
    setFiles(prevFiles => [...prevFiles, ...newFiles]);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
    },
    multiple: true
  });

  const handleUpload = async () => {
    if (files.length === 0) {
      toast({
        title: 'Lütfen dosya ekleyin',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    setUploading(true);
    const filePromises = files.map(async (fileObj) => {
      if (uploadSuccess.includes(fileObj.id)) {
        return null; // Skip already uploaded files
      }
      
      try {
        // Initialize progress
        setUploadProgress(prev => ({
          ...prev,
          [fileObj.id]: 0
        }));

        const formData = new FormData();
        formData.append('file', fileObj.file);
        formData.append('title', title || fileObj.file.name);
        formData.append('description', description || '');
        formData.append('enable_ocr', enableOcr.toString());

        // Upload with progress tracking
        const response = await api.uploadDocument(formData, (progress) => {
          setUploadProgress(prev => ({
            ...prev,
            [fileObj.id]: progress
          }));
        });

        setUploadSuccess(prev => [...prev, fileObj.id]);
        
        toast({
          title: 'Dosya yüklendi',
          description: `${fileObj.file.name} başarıyla yüklendi.`,
          status: 'success',
          duration: 5000,
          isClosable: true,
        });

        return response;
      } catch (error) {
        toast({
          title: 'Yükleme hatası',
          description: `${fileObj.file.name}: ${error.message || 'Bilinmeyen hata'}`,
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
        return null;
      }
    });

    await Promise.all(filePromises);
    setUploading(false);
  };

  const removeFile = (id) => {
    setFiles(files.filter(fileObj => fileObj.id !== id));
    setUploadProgress(prev => {
      const newProgress = { ...prev };
      delete newProgress[id];
      return newProgress;
    });
    setUploadSuccess(prev => prev.filter(successId => successId !== id));
  };

  const clearAll = () => {
    setFiles([]);
    setUploadProgress({});
    setUploadSuccess([]);
  };

  return (
    <Box p={6} maxW="1000px" mx="auto">
      <Heading mb={6}>Doküman Yükleme</Heading>
      
      <HStack spacing={6} align="flex-start" mb={6}>
        <Card flex="1" variant="outline">
          <CardBody>
            <Box
              {...getRootProps()}
              p={10}
              border="2px dashed"
              borderColor={isDragActive ? "brand.500" : "gray.300"}
              borderRadius="md"
              textAlign="center"
              bg={isDragActive ? "brand.50" : "transparent"}
              cursor="pointer"
              transition="all 0.3s"
              _hover={{ borderColor: "brand.500", bg: "brand.50" }}
            >
              <input {...getInputProps()} />
              <Icon as={FiUpload} w={10} h={10} color="gray.400" mb={4} />
              <Text fontSize="lg" fontWeight="medium">
                {isDragActive ? 'Dosyaları buraya bırakın' : 'Dosyaları sürükleyin veya seçmek için tıklayın'}
              </Text>
              <Text color="gray.500" mt={2}>
                PDF veya TXT dosyaları desteklenir
              </Text>
            </Box>
          </CardBody>
        </Card>
        
        <Card flex="1" variant="outline">
          <CardBody>
            <VStack spacing={4} align="stretch">
              <Heading size="sm" mb={2}>Doküman Bilgileri</Heading>
              
              <FormControl>
                <FormLabel>Başlık (opsiyonel)</FormLabel>
                <Input 
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Doküman başlığı"
                />
              </FormControl>
              
              <FormControl>
                <FormLabel>Açıklama (opsiyonel)</FormLabel>
                <Textarea 
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Doküman açıklaması"
                  rows={3}
                />
              </FormControl>
              
              <FormControl display="flex" alignItems="center">
                <FormLabel htmlFor="enable-ocr" mb="0">
                  OCR Aktif (PDF resim içeriyorsa)
                </FormLabel>
                <Switch 
                  id="enable-ocr"
                  isChecked={enableOcr}
                  onChange={() => setEnableOcr(!enableOcr)}
                  colorScheme="brand"
                />
              </FormControl>
            </VStack>
          </CardBody>
        </Card>
      </HStack>

      {files.length > 0 && (
        <Card variant="outline" mb={6}>
          <CardBody>
            <Flex justify="space-between" mb={4}>
              <Heading size="md">Yüklenecek Dosyalar ({files.length})</Heading>
              <Button size="sm" colorScheme="gray" onClick={clearAll}>
                Tümünü Temizle
              </Button>
            </Flex>
            
            <VStack spacing={4} align="stretch">
              {files.map((fileObj) => (
                <Box
                  key={fileObj.id}
                  p={4}
                  borderWidth="1px"
                  borderRadius="md"
                  position="relative"
                >
                  <Flex justify="space-between" align="center">
                    <Flex align="center">
                      <Icon as={FiFile} mr={3} color="gray.500" />
                      <Box>
                        <Text fontWeight="medium" noOfLines={1}>
                          {fileObj.file.name}
                        </Text>
                        <HStack spacing={2} mt={1}>
                          <Text fontSize="sm" color="gray.500">
                            {(fileObj.file.size / 1024 / 1024).toFixed(2)} MB
                          </Text>
                          <Tag size="sm" colorScheme={fileObj.file.type.includes('pdf') ? 'red' : 'blue'}>
                            {fileObj.file.type.includes('pdf') ? 'PDF' : 'TXT'}
                          </Tag>
                        </HStack>
                      </Box>
                    </Flex>
                    <Flex align="center">
                      {uploadSuccess.includes(fileObj.id) ? (
                        <Icon as={FiCheckCircle} color="green.500" mr={3} boxSize={5} />
                      ) : (
                        <Button
                          size="sm"
                          colorScheme="red"
                          variant="ghost"
                          onClick={() => removeFile(fileObj.id)}
                          isDisabled={uploading}
                          leftIcon={<FiTrash2 />}
                        >
                          Kaldır
                        </Button>
                      )}
                    </Flex>
                  </Flex>
                  
                  {(uploadProgress[fileObj.id] !== undefined && uploadProgress[fileObj.id] < 100) && (
                    <Progress
                      value={uploadProgress[fileObj.id]}
                      size="xs"
                      colorScheme="brand"
                      mt={2}
                    />
                  )}
                </Box>
              ))}
            </VStack>
          </CardBody>
        </Card>
      )}

      <Flex justify="space-between">
        <Box>
          <Alert status="info" borderRadius="md" maxW="md">
            <AlertIcon as={FiInfo} />
            Dokümanlar yükledikten sonra otomatik olarak işlenecek ve aranabilir hale gelecektir.
          </Alert>
        </Box>
        
        <Button
          colorScheme="brand"
          size="lg"
          leftIcon={<FiUpload />}
          onClick={handleUpload}
          isLoading={uploading}
          loadingText="Yükleniyor..."
          isDisabled={files.length === 0 || uploading}
        >
          Dosyaları Yükle
        </Button>
      </Flex>
    </Box>
  );
};

export default DocumentUpload;