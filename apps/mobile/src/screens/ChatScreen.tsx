import React, { useState, useEffect, useRef, useCallback } from "react";
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
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRoute, useNavigation } from "@react-navigation/native";
import {
  Ionicons,
  MaterialIcons,
  MaterialCommunityIcons,
} from "@expo/vector-icons";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import * as Haptics from "expo-haptics";
import { BlurView } from "expo-blur";

interface ChatMessage {
  id: string;
  content: string;
  user_id: string;
  user_name: string;
  user_avatar?: string;
  timestamp: string;
  message_type: "text" | "trade_proposal" | "lineup_share" | "achievement";
  status: "sent" | "delivered" | "read";
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
  role: "owner" | "admin" | "member";
  is_online: boolean;
  last_seen?: string;
}

interface TypingIndicator {
  user_id: string;
  user_name: string;
}

const { width: screenWidth, height: screenHeight } = Dimensions.get("window");

export default function ChatScreen() {
  const route = useRoute();
  const navigation = useNavigation();
  const { leagueId, leagueName } = route.params as any;

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [participants, setParticipants] = useState<ChatParticipant[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showParticipants, setShowParticipants] = useState(false);
  const [showReactions, setShowReactions] = useState(false);
  const [selectedMessage, setSelectedMessage] = useState<string | null>(null);
  const [typingUsers, setTypingUsers] = useState<TypingIndicator[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [currentUserId, setCurrentUserId] = useState<string>("");
  const [replyToMessage, setReplyToMessage] = useState<ChatMessage | null>(
    null,
  );

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
    const wsUrl = `${process.env.EXPO_PUBLIC_WS_URL || "ws://localhost:8000"}/ws/chat/${leagueId}`;
    websocketRef.current = new WebSocket(wsUrl);

    websocketRef.current.onopen = () => {
      console.log("WebSocket connected");
    };

    websocketRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case "message":
          setMessages((prev) => [...prev, data.message]);
          Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
          break;
        case "typing_start":
          setTypingUsers((prev) => [
            ...prev.filter((u) => u.user_id !== data.user_id),
            { user_id: data.user_id, user_name: data.user_name },
          ]);
          break;
        case "typing_stop":
          setTypingUsers((prev) =>
            prev.filter((u) => u.user_id !== data.user_id),
          );
          break;
        case "reaction_added":
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === data.message_id
                ? {
                    ...msg,
                    reactions: {
                      ...msg.reactions,
                      [data.emoji]: [
                        ...(msg.reactions[data.emoji] || []),
                        data.user_id,
                      ],
                    },
                  }
                : msg,
            ),
          );
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          break;
        case "message_pinned":
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === data.message_id ? { ...msg, is_pinned: true } : msg,
            ),
          );
          break;
      }
    };

    websocketRef.current.onclose = () => {
      console.log("WebSocket disconnected");
      setTimeout(() => {
        if (websocketRef.current?.readyState === WebSocket.CLOSED) {
          initializeWebSocket();
        }
      }, 3000);
    };

    websocketRef.current.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
  }, [leagueId]);

  const fetchMessages = async () => {
    try {
      const response = await fetch(
        `${process.env.EXPO_PUBLIC_API_URL}/api/leagues/${leagueId}/messages`,
      );
      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages || []);
        setParticipants(data.participants || []);
        setCurrentUserId(data.current_user_id || "");
      }
    } catch (error) {
      console.error("Error fetching messages:", error);
      Alert.alert("Error", "Failed to load messages");
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim()) return;

    const messageData = {
      content: newMessage,
      message_type: "text",
      thread_id: replyToMessage?.id,
    };

    try {
      const response = await fetch(
        `${process.env.EXPO_PUBLIC_API_URL}/api/leagues/${leagueId}/messages`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(messageData),
        },
      );

      if (response.ok) {
        setNewMessage("");
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
      console.error("Error sending message:", error);
      Alert.alert("Error", "Failed to send message");
    }
  };

  const addReaction = async (messageId: string, emoji: string) => {
    try {
      await fetch(
        `${process.env.EXPO_PUBLIC_API_URL}/api/leagues/${leagueId}/messages/${messageId}/reactions`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ emoji }),
        },
      );

      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      hideReactionModal();
    } catch (error) {
      console.error("Error adding reaction:", error);
    }
  };

  const pinMessage = async (messageId: string) => {
    try {
      await fetch(
        `${process.env.EXPO_PUBLIC_API_URL}/api/leagues/${leagueId}/messages/${messageId}/pin`,
        {
          method: "POST",
        },
      );
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (error) {
      console.error("Error pinning message:", error);
    }
  };

  const reportMessage = async (messageId: string) => {
    Alert.alert(
      "Report Message",
      "Are you sure you want to report this message?",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Report",
          style: "destructive",
          onPress: async () => {
            try {
              await fetch(
                `${process.env.EXPO_PUBLIC_API_URL}/api/leagues/${leagueId}/messages/${messageId}/report`,
                {
                  method: "POST",
                },
              );
              Alert.alert("Success", "Message reported successfully");
            } catch (error) {
              console.error("Error reporting message:", error);
              Alert.alert("Error", "Failed to report message");
            }
          },
        },
      ],
    );
  };

  const startTyping = () => {
    if (!isTyping && websocketRef.current?.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify({ type: "typing_start" }));
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
      websocketRef.current.send(JSON.stringify({ type: "typing_stop" }));
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

    if (diffMins < 1) return "now";
    if (diffMins < 60) return `${diffMins}m`;
    if (diffHours < 24) return `${diffHours}h`;
    return date.toLocaleDateString();
  };

  const getMessageTypeIcon = (type: string) => {
    switch (type) {
      case "trade_proposal":
        return "🤝";
      case "lineup_share":
        return "📋";
      case "achievement":
        return "🏆";
      default:
        return null;
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

  const renderMessage = ({
    item: message,
    index,
  }: {
    item: ChatMessage;
    index: number;
  }) => {
    const isOwnMessage = message.user_id === currentUserId;
    const showAvatar =
      index === 0 || messages[index - 1].user_id !== message.user_id;
    const showTimestamp =
      index === 0 ||
      new Date(message.timestamp).getTime() -
        new Date(messages[index - 1].timestamp).getTime() >
        300000;

    return (
      <View style={{ marginBottom: 16, paddingHorizontal: 16 }}>
        {showTimestamp && (
          <View style={{ alignItems: "center", marginBottom: 8 }}>
            <Text
              style={{
                fontSize: 12,
                color: "#6b7280",
                backgroundColor: "#f3f4f6",
                paddingHorizontal: 8,
                paddingVertical: 4,
                borderRadius: 9999,
              }}
            >
              {formatTimestamp(message.timestamp)}
            </Text>
          </View>
        )}

        <View
          style={{
            flexDirection: "row",
            justifyContent: isOwnMessage ? "flex-end" : "flex-start",
          }}
        >
          {!isOwnMessage && showAvatar && (
            <Image
              source={{
                uri:
                  message.user_avatar ||
                  `https://ui-avatars.com/api/?name=${message.user_name}&background=random`,
              }}
              style={{
                width: 32,
                height: 32,
                borderRadius: 16,
                marginRight: 8,
              }}
            />
          )}
          {!isOwnMessage && !showAvatar && (
            <View style={{ width: 32, marginRight: 8 }} />
          )}

          <View
            style={{
              maxWidth: "75%",
              alignItems: isOwnMessage ? "flex-end" : "flex-start",
            }}
          >
            {!isOwnMessage && showAvatar && (
              <View
                style={{
                  flexDirection: "row",
                  alignItems: "center",
                  marginBottom: 4,
                }}
              >
                <Text
                  style={{ fontSize: 12, fontWeight: "500", color: "#374151" }}
                >
                  {message.user_name}
                </Text>
                {getMessageTypeIcon(message.message_type) && (
                  <Text style={{ marginLeft: 4, fontSize: 12 }}>
                    {getMessageTypeIcon(message.message_type)}
                  </Text>
                )}
                {message.is_moderator_message && (
                  <View
                    style={{
                      marginLeft: 4,
                      backgroundColor: "#dbeafe",
                      paddingHorizontal: 4,
                      borderRadius: 4,
                    }}
                  >
                    <Text style={{ fontSize: 12, color: "#2563eb" }}>MOD</Text>
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
              style={{
                paddingHorizontal: 12,
                paddingVertical: 8,
                borderRadius: 20,
                backgroundColor: isOwnMessage
                  ? "#3b82f6"
                  : message.is_pinned
                    ? "#fef3c7"
                    : "#f3f4f6",
                borderWidth: message.is_pinned ? 1 : 0,
                borderColor: message.is_pinned ? "#f59e0b" : undefined,
              }}
            >
              {message.is_pinned && (
                <View
                  style={{
                    flexDirection: "row",
                    alignItems: "center",
                    marginBottom: 4,
                  }}
                >
                  <MaterialIcons name="push-pin" size={12} color="#f59e0b" />
                  <Text
                    style={{ fontSize: 12, color: "#f59e0b", marginLeft: 4 }}
                  >
                    Pinned
                  </Text>
                </View>
              )}

              <Text style={{ color: isOwnMessage ? "#ffffff" : "#1f2937" }}>
                {message.content}
              </Text>
            </TouchableOpacity>

            {/* Reactions */}
            {Object.keys(message.reactions).length > 0 && (
              <View
                style={{
                  flexDirection: "row",
                  flexWrap: "wrap",
                  marginTop: 4,
                  maxWidth: "100%",
                }}
              >
                {Object.entries(message.reactions).map(([emoji, userIds]) => (
                  <TouchableOpacity
                    key={emoji}
                    onPress={() => addReaction(message.id, emoji)}
                    style={{
                      backgroundColor: "white",
                      borderWidth: 1,
                      borderColor: "#e5e7eb",
                      borderRadius: 9999,
                      paddingHorizontal: 8,
                      paddingVertical: 4,
                      marginRight: 4,
                      marginBottom: 4,
                      flexDirection: "row",
                      alignItems: "center",
                    }}
                  >
                    <Text style={{ fontSize: 14 }}>{emoji}</Text>
                    <Text
                      style={{ fontSize: 12, color: "#6b7280", marginLeft: 4 }}
                    >
                      {userIds.length}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            )}

            <View
              style={{
                flexDirection: "row",
                alignItems: "center",
                marginTop: 4,
              }}
            >
              <Text
                style={{
                  fontSize: 12,
                  color: isOwnMessage ? "#93c5fd" : "#6b7280",
                }}
              >
                {formatTimestamp(message.timestamp)}
              </Text>
              {isOwnMessage && (
                <MaterialIcons
                  name={message.status === "read" ? "done-all" : "done"}
                  size={12}
                  color={message.status === "read" ? "#3b82f6" : "#9ca3af"}
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
              {typingUsers.map((u) => u.user_name).join(", ")}
              {typingUsers.length === 1 ? " is" : " are"} typing...
            </Text>
          </View>
        </View>
      </View>
    );
  };

  useEffect(() => {
    navigation.setOptions({
      title: leagueName || "League Chat",
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
      <SafeAreaView
        style={{
          flex: 1,
          backgroundColor: "white",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <MaterialIcons name="chat" size={48} color="#9ca3af" />
        <Text style={{ color: "#6b7280", marginTop: 16 }}>
          Loading messages...
        </Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: "white" }}>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        style={{ flex: 1 }}
      >
        {/* Reply indicator */}
        {replyToMessage && (
          <View
            style={{
              backgroundColor: "#eff6ff",
              paddingHorizontal: 16,
              paddingVertical: 8,
              borderBottomWidth: 1,
              borderBottomColor: "#bfdbfe",
            }}
          >
            <View
              style={{
                flexDirection: "row",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <View style={{ flex: 1 }}>
                <Text
                  style={{ color: "#2563eb", fontSize: 14, fontWeight: "500" }}
                >
                  Replying to {replyToMessage.user_name}
                </Text>
                <Text
                  style={{ color: "#3b82f6", fontSize: 14 }}
                  numberOfLines={1}
                >
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
          style={{ flex: 1 }}
          onContentSizeChange={scrollToBottom}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          ListFooterComponent={renderTypingIndicator}
        />

        {/* Input */}
        <View
          style={{
            paddingHorizontal: 16,
            paddingVertical: 8,
            borderTopWidth: 1,
            borderTopColor: "#e5e7eb",
          }}
        >
          <Animated.View
            style={{
              height: inputHeight,
              flexDirection: "row",
              alignItems: "flex-end",
            }}
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
              style={{
                flex: 1,
                borderWidth: 1,
                borderColor: "#d1d5db",
                borderRadius: 9999,
                paddingHorizontal: 16,
                paddingVertical: 8,
                marginRight: 8,
                maxHeight: 80,
                textAlignVertical: "center",
              }}
            />
            <TouchableOpacity
              onPress={sendMessage}
              disabled={!newMessage.trim()}
              style={{
                width: 40,
                height: 40,
                borderRadius: 9999,
                justifyContent: "center",
                alignItems: "center",
                backgroundColor: newMessage.trim() ? "#3b82f6" : "#d1d5db",
              }}
            >
              <MaterialIcons name="send" size={20} color="white" />
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
                    <Text className="text-lg font-semibold">
                      League Members
                    </Text>
                    <TouchableOpacity onPress={hideParticipantsModal}>
                      <MaterialIcons name="close" size={24} color="#374151" />
                    </TouchableOpacity>
                  </View>
                  <Text className="text-gray-500">
                    {participants.length} members
                  </Text>
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
                            uri:
                              participant.user_avatar ||
                              `https://ui-avatars.com/api/?name=${participant.user_name}&background=random`,
                          }}
                          className="w-10 h-10 rounded-full"
                        />
                        {participant.is_online && (
                          <View className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 border-2 border-white rounded-full" />
                        )}
                      </View>
                      <View className="flex-1 ml-3">
                        <View className="flex-row items-center">
                          <Text className="font-medium">
                            {participant.user_name}
                          </Text>
                          {participant.role === "owner" && (
                            <View className="ml-2 bg-red-100 px-2 py-1 rounded">
                              <Text className="text-xs text-red-600">
                                Owner
                              </Text>
                            </View>
                          )}
                          {participant.role === "admin" && (
                            <View className="ml-2 bg-blue-100 px-2 py-1 rounded">
                              <Text className="text-xs text-blue-600">
                                Admin
                              </Text>
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
            <Text className="text-center text-lg font-semibold mb-4">
              Add Reaction
            </Text>
            <View className="flex-row flex-wrap justify-center">
              {["❤️", "👍", "👎", "😂", "😮", "😢", "😡", "🔥", "👏", "🎉"].map(
                (emoji) => (
                  <TouchableOpacity
                    key={emoji}
                    onPress={() =>
                      selectedMessage && addReaction(selectedMessage, emoji)
                    }
                    className="w-12 h-12 justify-center items-center m-1 bg-gray-100 rounded-full"
                  >
                    <Text className="text-2xl">{emoji}</Text>
                  </TouchableOpacity>
                ),
              )}
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
                onPress={() =>
                  selectedMessage && reportMessage(selectedMessage)
                }
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
