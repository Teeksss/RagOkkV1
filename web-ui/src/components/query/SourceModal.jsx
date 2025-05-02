import React from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  Text,
  Box,
  Flex,
  HStack,
  Tag,
  Icon,
  VStack,
  Badge,
  Divider,
} from '@chakra-ui/react';
import { FiFileText, FiClock, FiBookmark, FiLink } from 'react-icons/fi';

const SourceModal = ({ isOpen, onClose, source }) => {
  if (!source) return null;

  const handleCopyText = () => {
    navigator.clipboard.writeText(source.content).then(
      () => {
        // Show success message (optional)
      },
      (err) => {
        console.error('Failed to copy text: ', err);
      }
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>
          <Flex align="center">
            <Icon as={FiFileText} mr={2} />
            <Text>Kaynak Bağlam</Text>
          </Flex>
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody>
          <VStack spacing={4} align="stretch">
            {/* Document Info */}
            <Box p={4} borderWidth="1px" borderRadius="md" bg="gray.50">
              <Text fontWeight="bold" mb={2}>
                {source.document?.title || 'Belge Başlığı'}
              </Text>
              
              <HStack spacing={4} mt={2} wrap="wrap">
                <Badge colorScheme="blue">
                  {source.document?.filename || 'unknown.pdf'}
                </Badge>
                
                {source.metadata?.chunk_index !== undefined && (
                  <Badge colorScheme="green">
                    Chunk: {source.metadata.chunk_index + 1}
                  </Badge>
                )}
                
                {source.metadata?.page_number && (
                  <Badge colorScheme="purple">
                    Sayfa: {source.metadata.page_number}
                  </Badge>
                )}
                
                <Badge colorScheme="orange">
                  Benzerlik: %{Math.round(source.score * 100)}
                </Badge>
              </HStack>
            </Box>
            
            <Divider />
            
            {/* Content */}
            <Box 
              p={4} 
              borderWidth="1px" 
              borderRadius="md"
              minHeight="200px"
              maxHeight="400px"
              overflowY="auto"
              whiteSpace="pre-wrap"
              fontSize="sm"
              fontFamily="monospace"
            >
              {source.content}
            </Box>
            
            {/* Metadata */}
            {source.metadata && Object.keys(source.metadata).length > 0 && (
              <>
                <Divider />
                <Box>
                  <Text fontWeight="bold" mb={2}>Metadata</Text>
                  <Box p={2} borderWidth="1px" borderRadius="md" bg="gray.50" fontSize="sm">
                    <pre>{JSON.stringify(source.metadata, null, 2)}</pre>
                  </Box>
                </Box>
              </>
            )}
          </VStack>
        </ModalBody>

        <ModalFooter>
          <Button variant="outline" mr={3} onClick={handleCopyText} leftIcon={<FiLink />}>
            Metni Kopyala
          </Button>
          <Button colorScheme="blue" onClick={onClose}>
            Kapat
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default SourceModal;