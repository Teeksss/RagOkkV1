import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Input,
  Button,
  VStack,
  HStack,
  Text,
  Spinner,
  useToast,
  Flex,
  Heading,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Tag,
  TagLabel,
  Icon,
  Card,
  CardBody,
  Divider,
  List,
  ListItem,
  Select,
  useDisclosure,
  IconButton,
  Badge,
  Tooltip,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
} from '@chakra-ui/react';
import { 
  FiSearch, 
  FiClock, 
  FiBookmark, 
  FiExternalLink, 
  FiFile, 
  FiFilter, 
  FiChevronDown,
  FiInfo,
  FiCheckCircle,
  FiDownload,
  FiRefreshCw,
} from 'react-icons/fi';
import { useApi } from '../../contexts/ApiContext';
import ReactMarkdown from 'react-markdown';
import SourceModal from './SourceModal';

const QueryInterface = () => {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [queryHistory, setQueryHistory] = useState([]);
  const [availableModels, setAvailableModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [sortBy, setSortBy] = useState('relevance');
  const [selectedSource, setSelectedSource] = useState(null);
  const { isOpen, onOpen, onClose } = useDisclosure();
  
  const inputRef = useRef(null);
  const toast = useToast();
  const { api } = useApi();

  // Load available models and query history on component mount
  useEffect(() => {
    const loadModels = async () => {
      try {
        const models = await api.getAvailableModels();
        setAvailableModels(models.models || []);
        setSelectedModel(models.default || null);
      } catch (err) {
        console.error('Error loading models:', err);
      }
    };
    
    if (inputRef.current) {
      inputRef.current.focus();
    }
    
    // Load query history from local storage
    const storedHistory = localStorage.getItem('queryHistory');
    if (storedHistory) {
      try {
        setQueryHistory(JSON.parse(storedHistory));
      } catch (e) {
        console.error('Error loading query history', e);
      }
    }
    
    loadModels();
  }, [api]);

  // Save query history to local storage
  useEffect(() => {
    if (queryHistory.length > 0) {
      localStorage.setItem('queryHistory', JSON.stringify(queryHistory));
    }
  }, [queryHistory]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!query.trim()) {
      toast({
        title: 'Lütfen bir soru girin',
        status: 'warning',
        duration: 2000,
        isClosable: true,
      });
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      // Call the API for the query
      const response = await api.getQueryResponse(query, selectedModel);
      setResults(response);
      
      // Add to query history (avoid duplicates)
      if (!queryHistory.some(item => item.query === query)) {
        setQueryHistory(prev => [
          { query, timestamp: new Date().toISOString(), model: selectedModel },
          ...prev.slice(0, 9) // Keep only last 10 queries
        ]);
      }
    } catch (err) {
      console.error('Error during query:', err);
      setError(err.message || 'Sorgulama sırasında bir hata oluştu');
      toast({
        title: 'Sorgulama hatası',
        description: err.message || 'Yanıt alınamadı',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleHistoryClick = (historicalQuery) => {
    setQuery(historicalQuery);
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  const handleClearHistory = () => {
    setQueryHistory([]);
    localStorage.removeItem('queryHistory');
  };
  
  const handleSourceClick = (source) => {
    setSelectedSource(source);
    onOpen();
  };
  
  const sortSources = (sources) => {
    if (!sources) return [];
    
    // Create a copy to avoid mutating the original
    const sortedSources = [...sources];
    
    switch (sortBy) {
      case 'relevance':
        return sortedSources.sort((a, b) => b.score - a.score);
      case 'document':
        return sortedSources.sort((a, b) => {
          const docA = a.document?.title || '';
          const docB = b.document?.title || '';
          return docA.localeCompare(docB);
        });
      case 'chunk':
        return sortedSources.sort((a, b) => {
          const chunkA = a.metadata?.chunk_index || 0;
          const chunkB = b.metadata?.chunk_index || 0;
          return chunkA - chunkB;
        });
      default:
        return sortedSources;
    }
  };
  
  const exportResults = () => {
    if (!results) return;
    
    const data = {
      query: results.query,
      answer: results.answer,
      sources: results.sources,
      context: results.context,
      model: results.model,
      timestamp: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `query-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    toast({
      title: 'Sonuçlar dışa aktarıldı',
      status: 'success',
      duration: 2000,
      isClosable: true,
    });
  };

  return (
    <Box p={6} maxW="1000px" mx="auto">
      <Heading mb={6}>Bilgi Arama</Heading>

      <HStack spacing={6} align="flex-start">
        <VStack spacing={6} flex="3" align="stretch">
          {/* Search Form */}
          <Card variant="outline">
            <CardBody>
              <form onSubmit={handleSubmit}>
                <VStack spacing={4}>
                  <Flex width="100%" wrap={{ base: 'wrap', md: 'nowrap' }} gap={2}>
                    <Input
                      ref={inputRef}
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder="Belgelerinizle ilgili bir soru sorun..."
                      size="lg"
                      flex="1"
                      minW={{ base: '100%', md: 'auto' }}
                      mr={{ base: 0, md: 2 }}
                      disabled={isLoading}
                    />
                    
                    <HStack spacing={2}>
                      <Select 
                        size="lg"
                        value={selectedModel || ''}
                        onChange={(e) => setSelectedModel(e.target.value)}
                        placeholder="Model"
                        disabled={isLoading || availableModels.length === 0}
                        minW={{ base: 'full', md: '120px' }}
                      >
                        {availableModels.map(model => (
                          <option key={model} value={model}>
                            {model}
                          </option>
                        ))}
                      </Select>
                      
                      <Button
                        colorScheme="brand"
                        size="lg"
                        type="submit"
                        isLoading={isLoading}
                        loadingText="Sorgulanıyor"
                        leftIcon={<FiSearch />}
                      >
                        Ara
                      </Button>
                    </HStack>
                  </Flex>
                </VStack>
              </form>
            </CardBody>
          </Card>

          {/* Results */}
          {isLoading && (
            <Flex justify="center" py={10}>
              <VStack>
                <Spinner size="xl" color="brand.500" thickness="4px" />
                <Text mt={4} color="gray.600">
                  Belgeleriniz taranıyor, lütfen bekleyin...
                </Text>
              </VStack>
            </Flex>
          )}

          {error && !isLoading && (
            <Box p={6} bg="red.50" borderRadius="md" borderWidth="1px" borderColor="red.300">
              <Text color="red.500">{error}</Text>
            </Box>
          )}

          {results && !isLoading && (
            <Card variant="outline">
              <CardBody>
                <VStack align="stretch" spacing={4}>
                  <Flex justify="space-between" align="center">
                    <Text fontSize="lg" fontWeight="bold">
                      {query}
                    </Text>
                    
                    <HStack spacing={2}>
                      <Tooltip label="Sonuçları indir">
                        <IconButton
                          icon={<FiDownload />}
                          size="sm"
                          variant="ghost"
                          onClick={exportResults}
                        />
                      </Tooltip>
                      
                      {results.model && (
                        <Badge colorScheme="blue">
                          {results.model}
                        </Badge>
                      )}
                    </HStack>
                  </Flex>
                  
                  <Divider />
                  
                  <Box className="markdown-content">
                    <ReactMarkdown>{results.answer}</ReactMarkdown>
                  </Box>
                  
                  {results.sources && results.sources.length > 0 && (
                    <Box mt={4}>
                      <Flex justify="space-between" align="center" mb={2}>
                        <Text fontWeight="medium">
                          Kaynaklar:
                        </Text>
                        
                        <Select
                          size="xs"
                          width="auto"
                          value={sortBy}
                          onChange={(e) => setSortBy(e.target.value)}
                        >
                          <option value="relevance">İlişkiye göre sırala</option>
                          <option value="document">Belgeye göre sırala</option>
                          <option value="chunk">Parçaya göre sırala</option>
                        </Select>
                      </Flex>
                      
                      <List spacing={2}>
                        {sortSources(results.sources).map((source, index) => (
                          <ListItem key={index}>
                            <HStack spacing={2}>
                              <Icon as={FiFile} color="gray.500" />
                              <Text>{source.title}</Text>
                              <Tag size="sm" colorScheme="brand" borderRadius="full">
                                <TagLabel>%{Math.round(source.score * 100)}</TagLabel>
                              </Tag>
                              <IconButton
                                icon={<FiExternalLink />}
                                size="xs"
                                variant="ghost"
                                aria-label="View source details"
                                onClick={() => {
                                  // Find context with matching source info
                                  const context = results.context?.find(ctx => ctx.id === source.id);
                                  if (context) {
                                    handleSourceClick(context);
                                  }
                                }}
                              />
                            </HStack>
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  )}
                  
                  {results.timing && (
                    <Text fontSize="sm" color="gray.500" mt={2}>
                      Yanıt süresi: {results.timing.toFixed(2)}s
                    </Text>
                  )}
                </VStack>
              </CardBody>
            </Card>
          )}
          
          {/* Context Chunks (when results are available) */}
          {results && results.context && results.context.length > 0 && (
            <Accordion allowToggle>
              <AccordionItem>
                <h2>
                  <AccordionButton>
                    <Box flex="1" textAlign="left" fontWeight="medium">
                      Kullanılan Doküman Parçaları
                    </Box>
                    <AccordionIcon />
                  </AccordionButton>
                </h2>
                <AccordionPanel pb={4}>
                  <VStack align="stretch" spacing={4}>
                    {sortSources(results.context).map((chunk, index) => (
                      <Box 
                        key={index}
                        p={3} 
                        borderWidth="1px" 
                        borderRadius="md"
                        borderColor="gray.200"
                        bg="gray.50"
                      >
                        <HStack mb={2} flexWrap="wrap" spacing={2}>
                          <Tag size="sm" colorScheme="blue">
                            <TagLabel>Doküman: {chunk.document?.title || 'Bilinmeyen'}</TagLabel>
                          </Tag>
                          
                          {chunk.metadata?.chunk_index !== undefined && (
                            <Tag size="sm" colorScheme="green">
                              <TagLabel>Parça: {chunk.metadata.chunk_index + 1}</TagLabel>
                            </Tag>
                          )}
                          
                          {chunk.metadata?.page_number && (
                            <Tag size="sm" colorScheme="purple">
                              <TagLabel>Sayfa: {chunk.metadata.page_number}</TagLabel>
                            </Tag>
                          )}
                          
                          <Tag size="sm" colorScheme="orange">
                            <TagLabel>Benzerlik: %{Math.round(chunk.score * 100)}</TagLabel>
                          </Tag>
                        </HStack>
                        
                        <Text noOfLines={3}>{chunk.content}</Text>
                        
                        <Button 
                          size="xs" 
                          variant="link" 
                          rightIcon={<FiExternalLink />}
                          mt={1}
                          onClick={() => handleSourceClick(chunk)}
                        >
                          Detaylı görüntüle
                        </Button>
                      </Box>
                    ))}
                  </VStack>
                </AccordionPanel>
              </AccordionItem>
            </Accordion>
          )}
        </VStack>
        
        {/* Query History */}
        <Card variant="outline" flex="1" maxW="300px" display={{ base: "none", md: "block" }}>
          <CardBody>
            <VStack spacing={4} align="stretch">
              <Flex justify="space-between" align="center">
                <HStack>
                  <Icon as={FiClock} color="gray.500" />
                  <Text fontWeight="medium">Arama Geçmişi</Text>
                </HStack>
                {queryHistory.length > 0 && (
                  <Button 
                    size="xs" 
                    colorScheme="gray" 
                    onClick={handleClearHistory}
                  >
                    Temizle
                  </Button>
                )}
              </Flex>
              
              <Divider />
              
              {queryHistory.length === 0 ? (
                <Text color="gray.500" fontSize="sm" textAlign="center" py={4}>
                  Arama geçmişi boş
                </Text>
              ) : (
                <VStack align="stretch" spacing={1} maxH="400px" overflowY="auto">
                  {queryHistory.map((item, index) => (
                    <Box 
                      key={index}
                      p={2}
                      borderRadius="md"
                      cursor="pointer"
                      _hover={{ bg: "gray.100" }}
                      onClick={() => handleHistoryClick(item.query)}
                    >
                      <Text fontSize="sm" noOfLines={1}>{item.query}</Text>
                      <HStack spacing={2} mt={1}>
                        <Text fontSize="xs" color="gray.500">
                          {new Date(item.timestamp).toLocaleString()}
                        </Text>
                        
                        {item.model && (
                          <Badge fontSize="xs" colorScheme="blue">{item.model}</Badge>
                        )}
                      </HStack>
                    </Box>
                  ))}
                </VStack>
              )}
            </VStack>
          </CardBody>
        </Card>
      </HStack>
      
      {/* Source Modal */}
      <SourceModal 
        isOpen={isOpen} 
        onClose={onClose} 
        source={selectedSource} 
      />
    </Box>
  );
};

export default QueryInterface;