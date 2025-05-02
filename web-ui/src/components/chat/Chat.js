import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Flex,
  Text,
  Input,
  Button,
  VStack,
  HStack,
  Avatar,
  Spinner,
  IconButton,
  useToast,
  Divider,
  Tag,
  TagLabel,
  Tooltip,
  Card,
  CardBody,
  Heading,
} from '@chakra-ui/react';
import { FiSend, FiThumbsUp, FiThumbsDown, FiLink } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import { useApi } from '../../contexts/ApiContext';
import { useAuth } from '../../contexts/AuthContext';

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const endOfMessagesRef = useRef(null);
  const inputRef = useRef(null);
  const toast = useToast();
  const { api } = useApi();
  const { user } = useAuth();

  useEffect(() => {
    // Focus input on component mount
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  useEffect(() => {
    // Scroll to bottom whenever messages change
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (e) => {
    e?.preventDefault();
    
    if (!input.trim()) return;
    
    const userMessage = {
      content: input,
      role: 'user',
      timestamp: new Date().toISOString(),
    };
    
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setInput('');
    setLoading(true);
    
    try {
      const response = await api.sendChatMessage({
        query: userMessage.content,
        conversation_id: conversationId
      });
      
      setConversationId(response.conversation_id);
      
      const assistantMessage = {
        content: response.response,
        role: 'assistant',
        timestamp: response.timestamp,
        sources: response.sources || []
      };
      
      setMessages(prevMessages => [...prevMessages, assistantMessage]);
    } catch (error) {
      toast({
        title: 'Yanıt alınamadı',
        description: error.message || 'Bir hata oluştu',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
      
      // Add error message
      setMessages(prevMessages => [
        ...prevMessages,
        {
          content: 'Üzgünüm, yanıt alınırken bir hata oluştu. Lütfen tekrar deneyin.',
          role: 'assistant',
          timestamp: new Date().toISOString(),
          error: true
        }
      ]);
    } finally {
      setLoading(false);
      if (inputRef.current) {
        inputRef.current.focus();
      }
    }
  };

  const handleFeedback = async (messageIndex, isPositive) => {
    try {
      const message = messages[messageIndex];
      
      if (message.role !== 'assistant') return;
      
      await api.sendFeedback({
        query_id: conversationId,
        response_id: message.timestamp,
        rating: isPositive ? 5 : 1,
        feedback_text: isPositive ? 'Helpful response' : 'Not helpful'
      });
      
      // Update message to show feedback was given
      const updatedMessages = [...messages];
      updatedMessages[messageIndex] = {
        ...message,
        feedback: isPositive ? 'positive' : 'negative'
      };
      setMessages(updatedMessages);
      
      toast({
        title: isPositive ? 'Teşekkürler!' : 'Geri bildirim için teşekkürler',
        description: isPositive ? 'Olumlu geri bildiriminiz için teşekkürler' : 'Geri bildiriminiz için teşekkürler, daha iyi yanıtlar için çalışacağız',
        status: isPositive ? 'success' : 'info',
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: 'Geri bildirim gönderilemedi',
        description: error.message || 'Bir hata oluştu',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(
      () => {
        toast({
          title: 'Kopyalandı!',
          description: 'Mesaj panoya kopyalandı',
          status: 'success',
          duration: 2000,
        });
      },
      (err) => {
        toast({
          title: 'Kopyalanamadı',
          description: 'Mesaj kopyalanamadı: ' + err.message,
          status: 'error',
          duration: 3000,
        });
      }
    );
  };

  return (
    <Box p={6} maxW="1000px" mx="auto" h="calc(100vh - 80px)" display="flex" flexDirection="column">
      <Heading mb={6}>Sohbet</Heading>
      
      <Card variant="outline" flex="1" mb={4} overflow="hidden">
        <CardBody p={0} display="flex" flexDirection="column">
          <Box flex="1" overflowY="auto" p={4}>
            {messages.length === 0 ? (
              <Flex
                direction="column"
                align="center"
                justify="center"
                textAlign="center"
                h="100%"
                color="gray.500"
              >
                <Text fontSize="xl" mb={4}>Hoş geldiniz!</Text>
                <Text>Belgelerinizle ilgili herhangi bir soru sorabilirsiniz.</Text>
              </Flex>
            ) : (
              <VStack spacing={6} align="stretch">
                {messages.map((message, index) => (
                  <Box key={index}>
                    <Flex>
                      <Avatar 
                        size="sm" 
                        name={message.role === 'user' ? user?.name : 'AI Assistant'} 
                        src={message.role === 'user' ? user?.avatarUrl : '/assistant-avatar.png'} 
                        bg={message.role === 'assistant' ? 'brand.500' : 'gray.400'}
                        mr={3}
                      />
                      <Box flex="1">
                        <Flex justify="space-between" mb={1}>
                          <Text fontWeight="bold">
                            {message.role === 'user' ? 'Siz' : 'AI Asistan'}
                          </Text>
                          <Text fontSize="xs" color="gray.500">
                            {new Date(message.timestamp).toLocaleTimeString()}
                          </Text>
                        </Flex>
                        
                        <Box
                          p={3}
                          borderRadius="lg"
                          bg={message.role === 'assistant' ? 'gray.50' : 'brand.50'}
                          borderWidth="1px"
                          borderColor={message.role === 'assistant' ? 'gray.200' : 'brand.100'}
                        >
                          <Box className="markdown-content">
                            <ReactMarkdown>
                              {message.content}
                            </ReactMarkdown>
                          </Box>
                          
                          {message.sources && message.sources.length > 0 && (
                            <Box mt={3}>
                              <Divider mb={2} />
                              <Text fontSize="sm" fontWeight="medium" mb={1}>
                                Kaynaklar:
                              </Text>
                              <HStack spacing={2} flexWrap="wrap">
                                {message.sources.map((source, sourceIndex) => (
                                  <Tag 
                                    size="sm" 
                                    key={sourceIndex} 
                                    colorScheme="gray" 
                                    borderRadius="full"
                                  >
                                    <TagLabel>{source.title || `Belge ${source.id}`}</TagLabel>
                                  </Tag>
                                ))}
                              </HStack>
                            </Box>
                          )}
                        </Box>
                        
                        {message.role === 'assistant' && !message.error && (
                          <HStack mt={2} spacing={2} justify="flex-end">
                            <Tooltip label="Faydalı">
                              <IconButton
                                icon={<FiThumbsUp />}
                                size="xs"
                                variant={message.feedback === 'positive' ? 'solid' : 'ghost'}
                                colorScheme={message.feedback === 'positive' ? 'green' : 'gray'}
                                onClick={() => handleFeedback(index, true)}
                                isDisabled={message.feedback !== undefined}
                              />
                            </Tooltip>
                            <Tooltip label="Faydalı değil">
                              <IconButton
                                icon={<FiThumbsDown />}
                                size="xs"
                                variant={message.feedback === 'negative' ? 'solid' : 'ghost'}
                                colorScheme={message.feedback === 'negative' ? 'red' : 'gray'}
                                onClick={() => handleFeedback(index, false)}
                                isDisabled={message.feedback !== undefined}
                              />
                            </Tooltip>
                            <Tooltip label="Kopyala">
                              <IconButton
                                icon={<FiLink />}
                                size="xs"
                                variant="ghost"
                                onClick={() => copyToClipboard(message.content)}
                              />
                            </Tooltip>
                          </HStack>
                        )}
                      </Box>
                    </Flex>
                  </Box>
                ))}
                <div ref={endOfMessagesRef} />
              </VStack>
            )}
          </Box>
          
          {loading && (
            <Flex
              align="center"
              p={4}
              borderTopWidth="1px"
              borderColor="gray.200"
            >
              <Spinner size="sm" mr={3} color="brand.500" />
              <Text fontSize="sm">AI yanıt üretiyor...</Text>
            </Flex>
          )}
          
          <Flex
            as="form"
            p={4}
            borderTopWidth="1px"
            borderColor="gray.200"
            onSubmit={handleSendMessage}
          >
            <Input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Bir soru sorun..."
              mr={2}
              size="lg"
              disabled={loading}
            />
            <Button
              colorScheme="brand"
              px={6}
              size="lg"
              type="submit"
              isLoading={loading}
              leftIcon={<FiSend />}
              isDisabled={!input.trim() || loading}
            >
              Gönder
            </Button>
          </Flex>
        </CardBody>
      </Card>
    </Box>
  );
};

export default Chat;