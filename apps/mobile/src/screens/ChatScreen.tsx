import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TextInput,
  TouchableOpacity,
  Alert,
  Modal,
  Animated,
  Dimensions,
  KeyboardAvoidingView,
  Platform,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRoute, useNavigation } from '@react-navigation/native';
import {
  Ionicons,
  MaterialIcons,
  MaterialCommunityIcons,
} from '@expo/vector-icons';
import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import * as Haptics from 'expo-haptics';
import { BlurView } from 'expo-blur';

interface ChatMessage {
  id: string;
  content: string;
  user_id: string;
  user_name: string;
  user_avatar?: string;
  timestamp: string;
  message_type: 'text' | 'trade_proposal' | 'lineup_share' | 'achievement';
  status: 'sent' | 'delivered' | 'read';
  thread_id?: string;
  parent_message_id?: string;
  reactions: { [emoji: string]: string[] };
  attachments?: any[];
  is_pinned: boolean;
  is_moderator_message: boolean;
}

interface ChatParticipant {
  user_id: string;
  user_name: string;
  user_avatar?: string;
  role: 'owner' | 'admin' | 'member';
  is_online: boolean;
  last_seen?: string;
}

interface TypingIndicator {
  user_id: string;
  user_name: string;
}

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

export default function ChatScreen() {
  const route = useRoute();
  const navigation = useNavigation();
  const { leagueId, leagueName } = route.params as any;

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [participants, setParticipants] = useState<ChatParticipant[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showParticipants, setShowParticipants] = useState(false);
  const [showReactions, setShowReactions] = useState(false);
  const [selectedMessage, setSelectedMessage] = useState<string | null>(null);
  const [typingUsers, setTypingUsers] = useState<TypingIndicator[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [currentUserId, setCurrentUserId] = useState<string>('');
  const [replyToMessage, setReplyToMessage] = useState<ChatMessage | null>(null);

  const flatListRef = useRef<FlatList>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const slideAnim = useRef(new Animated.Value(screenWidth)).current;
  const reactionAnim = useRef(new Animated.Value(0)).current;
  const inputHeight = useRef(new Animated.Value(40)).current;

  const scrollToBottom = useCallback(() => {
    flatListRef.current?.scrollToEnd({ animated: true });
  }, []);

  const initializeWebSocket = useCallback(() => {
    const wsUrl = `${process.env.EXPO_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws/chat/${leagueId}`;
    websocketRef.current = new WebSocket(wsUrl);

    websocketRef.current.onopen = () => {
      console.log('WebSocket connected');
    };

    websocketRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'message':
          setMessages(prev => [...prev, data.message]);
          Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
          break;
        case 'typing_start':
          setTypingUsers(prev => [
            ...prev.filter(u => u.user_id !== data.user_id),
            { user_id: data.user_id, user_name: data.user_name }
          ]);
          break;
        case 'typing_stop':
          setTypingUsers(prev => prev.filter(u => u.user_id !== data.user_id));
          break;
        case 'reaction_added':
          setMessages(prev => prev.map(msg =>
            msg.id === data.message_id
              ? {
                  ...msg,
                  reactions: {
                    ...msg.reactions,
                    [data.emoji]: [...(msg.reactions[data.emoji] || []), data.user_id]
                  }
                }
              : msg
          ));
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          break;
        case 'message_pinned':
          setMessages(prev => prev.map(msg =>
            msg.id === data.message_id ? { ...msg, is_pinned: true } : msg
          ));
          break;
      }
    };

    websocketRef.current.onclose = () => {
      console.log('WebSocket disconnected');
      setTimeout(() => {
        if (websocketRef.current?.readyState === WebSocket.CLOSED) {
          initializeWebSocket();
        }
      }, 3000);
    };

    websocketRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }, [leagueId]);

  const fetchMessages = async () => {
    try {
      const response = await fetch(`${process.env.EXPO_PUBLIC_API_URL}/api/leagues/${leagueId}/messages`);
      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages || []);
        setParticipants(data.participants || []);
        setCurrentUserId(data.current_user_id || '');
      }
    } catch (error) {
      console.error('Error fetching messages:', error);
      Alert.alert('Error', 'Failed to load messages');
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim()) return;

    const messageData = {
      content: newMessage,
      message_type: 'text',
      thread_id: replyToMessage?.id
    };

    try {
      const response = await fetch(`${process.env.EXPO_PUBLIC_API_URL}/api/leagues/${leagueId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(messageData),
      });

      if (response.ok) {
        setNewMessage('');
        setReplyToMessage(null);
        stopTyping();
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

        Animated.timing(inputHeight, {
          toValue: 40,
          duration: 200,
          useNativeDriver: false,
        }).start();
      }
    } catch (error) {
      console.error('Error sending message:', error);
      Alert.alert('Error', 'Failed to send message');
    }
  };

  const addReaction = async (messageId: string, emoji: string) => {
    try {
      await fetch(`${process.env.EXPO_PUBLIC_API_URL}/api/leagues/${leagueId}/messages/${messageId}/reactions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ emoji }),
      });

      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      hideReactionModal();
    } catch (error) {
      console.error('Error adding reaction:', error);
    }
  };

  const pinMessage = async (messageId: string) => {
    try {
      await fetch(`${process.env.EXPO_PUBLIC_API_URL}/api/leagues/${leagueId}/messages/${messageId}/pin`, {
        method: 'POST',
      });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (error) {
      console.error('Error pinning message:', error);
    }
  };

  const reportMessage = async (messageId: string) => {
    Alert.alert(
      'Report Message',
      'Are you sure you want to report this message?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Report',
          style: 'destructive',
          onPress: async () => {
            try {
              await fetch(`${process.env.EXPO_PUBLIC_API_URL}/api/leagues/${leagueId}/messages/${messageId}/report`, {
                method: 'POST',
              });
              Alert.alert('Success', 'Message reported successfully');
            } catch (error) {
              console.error('Error reporting message:', error);
              Alert.alert('Error', 'Failed to report message');
            }
          }
        }
      ]
    );
  };

  const startTyping = () => {
    if (!isTyping && websocketRef.current?.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify({ type: 'typing_start' }));
      setIsTyping(true);
    }

    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    typingTimeoutRef.current = setTimeout(() => {
      stopTyping();
    }, 3000);
  };

  const stopTyping = () => {
    if (isTyping && websocketRef.current?.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify({ type: 'typing_stop' }));
      setIsTyping(false);
    }

    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
  };

  const showReactionModal = (messageId: string) => {
    setSelectedMessage(messageId);
    setShowReactions(true);
    Animated.spring(reactionAnim, {
      toValue: 1,
      useNativeDriver: true,
    }).start();
  };

  const hideReactionModal = () => {
    Animated.spring(reactionAnim, {
      toValue: 0,
      useNativeDriver: true,
    }).start(() => {
      setShowReactions(false);
      setSelectedMessage(null);
    });
  };

  const showParticipantsModal = () => {
    setShowParticipants(true);
    Animated.timing(slideAnim, {
      toValue: 0,
      duration: 300,
      useNativeDriver: true,
    }).start();
  };

  const hideParticipantsModal = () => {
    Animated.timing(slideAnim, {
      toValue: screenWidth,
      duration: 300,
      useNativeDriver: true,
    }).start(() => {
      setShowParticipants(false);
    });
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchMessages();
    setRefreshing(false);
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

    if (diffMins < 1) return 'now';
    if (diffMins < 60) return `${diffMins}m`;
    if (diffHours < 24) return `${diffHours}h`;
    return date.toLocaleDateString();
  };

  const getMessageTypeIcon = (type: string) => {
    switch (type) {
      case 'trade_proposal': return '🤝';
      case 'lineup_share': return '📋';
      case 'achievement': return '🏆';
      default: return null;
    }
  };

  const handleInputFocus = () => {
    Animated.timing(inputHeight, {
      toValue: 80,
      duration: 200,
      useNativeDriver: false,
    }).start();
  };

  const handleInputBlur = () => {
    if (!newMessage.trim()) {
      Animated.timing(inputHeight, {
        toValue: 40,
        duration: 200,
        useNativeDriver: false,
      }).start();
    }
  };

  const renderMessage = ({ item: message, index }: { item: ChatMessage; index: number }) => {
    const isOwnMessage = message.user_id === currentUserId;
    const showAvatar = index === 0 || messages[index - 1].user_id !== message.user_id;
    const showTimestamp = index === 0 ||
      new Date(message.timestamp).getTime() - new Date(messages[index - 1].timestamp).getTime() > 300000;

    return (
      <View className="mb-4 px-4">
        {showTimestamp && (
          <View className="items-center mb-2">
            <Text className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
              {formatTimestamp(message.timestamp)}
            </Text>
          </View>
        )}

        <View className={`flex-row ${isOwnMessage ? 'justify-end' : 'justify-start'}`}>
          {!isOwnMessage && showAvatar && (
            <Image
              source={{ uri: message.user_avatar || `https://ui-avatars.com/api/?name=${message.user_name}&background=random` }}
              className="w-8 h-8 rounded-full mr-2"
            />
          )}
          {!isOwnMessage && !showAvatar && <View className="w-8 mr-2" />}

          <View className={`max-w-[75%] ${isOwnMessage ? 'items-end' : 'items-start'}`}>
            {!isOwnMessage && showAvatar && (
              <View className="flex-row items-center mb-1">
                <Text className="text-xs font-medium text-gray-700">{message.user_name}</Text>
                {getMessageTypeIcon(message.message_type) && (
                  <Text className="ml-1 text-xs">{getMessageTypeIcon(message.message_type)}</Text>
                )}
                {message.is_moderator_message && (
                  <View className="ml-1 bg-blue-100 px-1 rounded">
                    <Text className="text-xs text-blue-600">MOD</Text>
                  </View>
                )}
              </View>
            )}

            <TouchableOpacity
              onLongPress={() => showReactionModal(message.id)}
              onPress={() => {
                if (replyToMessage?.id === message.id) {
                  setReplyToMessage(null);
                } else {
                  setReplyToMessage(message);
                }
              }}
              className={`px-3 py-2 rounded-2xl ${
                isOwnMessage
                  ? 'bg-blue-500'
                  : message.is_pinned
                    ? 'bg-yellow-100 border border-yellow-300'
                    : 'bg-gray-100'
              }`}
            >
              {message.is_pinned && (
                <View className="flex-row items-center mb-1">
                  <MaterialIcons name="push-pin" size={12} color="#f59e0b" />
                  <Text className="text-xs text-yellow-600 ml-1">Pinned</Text>
                </View>
              )}

              <Text className={`${isOwnMessage ? 'text-white' : 'text-gray-800'}`}>
                {message.content}
              </Text>
            </TouchableOpacity>

            {/* Reactions */}
            {Object.keys(message.reactions).length > 0 && (
              <View className="flex-row flex-wrap mt-1 max-w-full">
                {Object.entries(message.reactions).map(([emoji, userIds]) => (
                  <TouchableOpacity
                    key={emoji}
                    onPress={() => addReaction(message.id, emoji)}
                    className="bg-white border border-gray-200 rounded-full px-2 py-1 mr-1 mb-1 flex-row items-center"
                  >
                    <Text className="text-sm">{emoji}</Text>
                    <Text className="text-xs text-gray-600 ml-1">{userIds.length}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            )}

            <View className="flex-row items-center mt-1">
              <Text className={`text-xs ${isOwnMessage ? 'text-blue-200' : 'text-gray-500'}`}>
                {formatTimestamp(message.timestamp)}
              </Text>
              {isOwnMessage && (
                <MaterialIcons
                  name={message.status === 'read' ? 'done-all' : 'done'}
                  size={12}
                  color={message.status === 'read' ? '#3b82f6' : '#9ca3af'}
                  style={{ marginLeft: 4 }}
                />
              )}
            </View>
          </View>
        </View>
      </View>
    );
  };

  const renderTypingIndicator = () => {
    if (typingUsers.length === 0) return null;

    return (
      <View className="px-4 mb-2">
        <View className="flex-row items-center">
          <View className="w-8 mr-2" />
          <View className="bg-gray-100 px-3 py-2 rounded-2xl">
            <Text className="text-gray-500 text-sm">
              {typingUsers.map(u => u.user_name).join(', ')}
              {typingUsers.length === 1 ? ' is' : ' are'} typing...
            </Text>
          </View>
        </View>
      </View>
    );
  };

  useEffect(() => {
    navigation.setOptions({
      title: leagueName || 'League Chat',
      headerRight: () => (
        <TouchableOpacity onPress={showParticipantsModal} className="mr-4">
          <MaterialIcons name="people" size={24} color="#3b82f6" />
        </TouchableOpacity>
      ),
    });

    fetchMessages();
    initializeWebSocket();

    return () => {
      if (websocketRef.current) {
        websocketRef.current.close();
      }
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, [leagueId, navigation, leagueName, initializeWebSocket]);

  if (isLoading) {
    return (
      <SafeAreaView className="flex-1 bg-white justify-center items-center">
        <MaterialIcons name="chat" size={48} color="#9ca3af" />
        <Text className="text-gray-500 mt-4">Loading messages...</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView className="flex-1 bg-white">
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        className="flex-1"
      >
        {/* Reply indicator */}
        {replyToMessage && (
          <View className="bg-blue-50 px-4 py-2 border-b border-blue-200">
            <View className="flex-row items-center justify-between">
              <View className="flex-1">
                <Text className="text-blue-600 text-sm font-medium">
                  Replying to {replyToMessage.user_name}
                </Text>
                <Text className="text-blue-500 text-sm" numberOfLines={1}>
                  {replyToMessage.content}
                </Text>
              </View>
              <TouchableOpacity onPress={() => setReplyToMessage(null)}>
                <MaterialIcons name="close" size={20} color="#3b82f6" />
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Messages */}
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={(item) => item.id}
          renderItem={renderMessage}
          className="flex-1"
          onContentSizeChange={scrollToBottom}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          ListFooterComponent={renderTypingIndicator}
        />

        {/* Input */}
        <View className="px-4 py-2 border-t border-gray-200">
          <Animated.View
            style={{ height: inputHeight }}
            className="flex-row items-end"
          >
            <TextInput
              value={newMessage}
              onChangeText={(text) => {
                setNewMessage(text);
                startTyping();
              }}
              onFocus={handleInputFocus}
              onBlur={handleInputBlur}
              placeholder="Type a message..."
              multiline
              className="flex-1 border border-gray-300 rounded-full px-4 py-2 mr-2 max-h-20"
              style={{ textAlignVertical: 'center' }}
            />
            <TouchableOpacity
              onPress={sendMessage}
              disabled={!newMessage.trim()}
              className={`w-10 h-10 rounded-full justify-center items-center ${
                newMessage.trim() ? 'bg-blue-500' : 'bg-gray-300'
              }`}
            >
              <MaterialIcons
                name="send"
                size={20}
                color="white"
              />
            </TouchableOpacity>
          </Animated.View>
        </View>
      </KeyboardAvoidingView>

      {/* Participants Modal */}
      <Modal visible={showParticipants} transparent animationType="none">
        <View className="flex-1">
          <TouchableOpacity
            className="flex-1 bg-black/50"
            onPress={hideParticipantsModal}
          />
          <Animated.View
            style={{ transform: [{ translateX: slideAnim }] }}
            className="absolute right-0 top-0 bottom-0 w-80 bg-white"
          >
            <BlurView intensity={100} className="flex-1">
              <SafeAreaView className="flex-1">
                <View className="px-4 py-4 border-b border-gray-200">
                  <View className="flex-row items-center justify-between">
                    <Text className="text-lg font-semibold">League Members</Text>
                    <TouchableOpacity onPress={hideParticipantsModal}>
                      <MaterialIcons name="close" size={24} color="#374151" />
                    </TouchableOpacity>
                  </View>
                  <Text className="text-gray-500">{participants.length} members</Text>
                </View>

                <FlatList
                  data={participants}
                  keyExtractor={(item) => item.user_id}
                  className="flex-1"
                  renderItem={({ item: participant }) => (
                    <View className="px-4 py-3 flex-row items-center">
                      <View className="relative">
                        <Image
                          source={{
                            uri: participant.user_avatar ||
                            `https://ui-avatars.com/api/?name=${participant.user_name}&background=random`
                          }}
                          className="w-10 h-10 rounded-full"
                        />
                        {participant.is_online && (
                          <View className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 border-2 border-white rounded-full" />
                        )}
                      </View>
                      <View className="flex-1 ml-3">
                        <View className="flex-row items-center">
                          <Text className="font-medium">{participant.user_name}</Text>
                          {participant.role === 'owner' && (
                            <View className="ml-2 bg-red-100 px-2 py-1 rounded">
                              <Text className="text-xs text-red-600">Owner</Text>
                            </View>
                          )}
                          {participant.role === 'admin' && (
                            <View className="ml-2 bg-blue-100 px-2 py-1 rounded">
                              <Text className="text-xs text-blue-600">Admin</Text>
                            </View>
                          )}
                        </View>
                        {!participant.is_online && participant.last_seen && (
                          <Text className="text-xs text-gray-500">
                            Last seen {formatTimestamp(participant.last_seen)}
                          </Text>
                        )}
                      </View>
                    </View>
                  )}
                />
              </SafeAreaView>
            </BlurView>
          </Animated.View>
        </View>
      </Modal>

      {/* Reaction Modal */}
      <Modal visible={showReactions} transparent animationType="none">
        <TouchableOpacity
          className="flex-1 justify-center items-center bg-black/50"
          onPress={hideReactionModal}
        >
          <Animated.View
            style={{
              transform: [{ scale: reactionAnim }],
              opacity: reactionAnim,
            }}
            className="bg-white rounded-2xl p-4 mx-8"
          >
            <Text className="text-center text-lg font-semibold mb-4">Add Reaction</Text>
            <View className="flex-row flex-wrap justify-center">
              {['❤️', '👍', '👎', '😂', '😮', '😢', '😡', '🔥', '👏', '🎉'].map(emoji => (
                <TouchableOpacity
                  key={emoji}
                  onPress={() => selectedMessage && addReaction(selectedMessage, emoji)}
                  className="w-12 h-12 justify-center items-center m-1 bg-gray-100 rounded-full"
                >
                  <Text className="text-2xl">{emoji}</Text>
                </TouchableOpacity>
              ))}
            </View>

            <View className="flex-row justify-center mt-4 space-x-4">
              <TouchableOpacity
                onPress={() => selectedMessage && pinMessage(selectedMessage)}
                className="flex-row items-center bg-blue-100 px-4 py-2 rounded-full"
              >
                <MaterialIcons name="push-pin" size={16} color="#3b82f6" />
                <Text className="ml-2 text-blue-600">Pin</Text>
              </TouchableOpacity>

              <TouchableOpacity
                onPress={() => selectedMessage && reportMessage(selectedMessage)}
                className="flex-row items-center bg-red-100 px-4 py-2 rounded-full"
              >
                <MaterialIcons name="flag" size={16} color="#ef4444" />
                <Text className="ml-2 text-red-600">Report</Text>
              </TouchableOpacity>
            </View>
          </Animated.View>
        </TouchableOpacity>
      </Modal>
    </SafeAreaView>
  );
}