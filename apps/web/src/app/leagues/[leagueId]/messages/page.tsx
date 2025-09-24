'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Send,
  Reply,
  Heart,
  MessageCircle,
  MoreVertical,
  Pin,
  Flag,
  Search,
  Filter,
  Users
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';

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

export default function LeagueMessagesPage() {
  const params = useParams();
  const leagueId = params.leagueId as string;
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [participants, setParticipants] = useState<ChatParticipant[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedThread, setSelectedThread] = useState<string | null>(null);
  const [typingUsers, setTypingUsers] = useState<TypingIndicator[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [currentUserId, setCurrentUserId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const initializeWebSocket = useCallback(() => {
    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws/chat/${leagueId}`;
    websocketRef.current = new WebSocket(wsUrl);

    websocketRef.current.onopen = () => {
      console.log('WebSocket connected');
    };

    websocketRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'message':
          setMessages(prev => [...prev, data.message]);
          scrollToBottom();
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
      // Attempt to reconnect after 3 seconds
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
      const response = await fetch(`/api/leagues/${leagueId}/messages`);
      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages || []);
        setParticipants(data.participants || []);
        setCurrentUserId(data.current_user_id || '');
      }
    } catch (error) {
      console.error('Error fetching messages:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim()) return;

    const messageData = {
      content: newMessage,
      message_type: 'text',
      thread_id: selectedThread
    };

    try {
      const response = await fetch(`/api/leagues/${leagueId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(messageData),
      });

      if (response.ok) {
        setNewMessage('');
        stopTyping();
      }
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const addReaction = async (messageId: string, emoji: string) => {
    try {
      await fetch(`/api/leagues/${leagueId}/messages/${messageId}/reactions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ emoji }),
      });
    } catch (error) {
      console.error('Error adding reaction:', error);
    }
  };

  const pinMessage = async (messageId: string) => {
    try {
      await fetch(`/api/leagues/${leagueId}/messages/${messageId}/pin`, {
        method: 'POST',
      });
    } catch (error) {
      console.error('Error pinning message:', error);
    }
  };

  const reportMessage = async (messageId: string) => {
    try {
      await fetch(`/api/leagues/${leagueId}/messages/${messageId}/report`, {
        method: 'POST',
      });
    } catch (error) {
      console.error('Error reporting message:', error);
    }
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

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setNewMessage(e.target.value);
    startTyping();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const filteredMessages = messages.filter(message =>
    searchTerm === '' ||
    message.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
    message.user_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const pinnedMessages = filteredMessages.filter(msg => msg.is_pinned);
  const regularMessages = filteredMessages.filter(msg => !msg.is_pinned);

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
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

  useEffect(() => {
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
  }, [leagueId, initializeWebSocket]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar - Participants */}
      <div className="w-80 border-r bg-card">
        <div className="p-4 border-b">
          <div className="flex items-center gap-2 mb-4">
            <Users className="h-5 w-5" />
            <h2 className="font-semibold">League Members</h2>
            <Badge variant="secondary">{participants.length}</Badge>
          </div>
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search messages..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8"
            />
          </div>
        </div>

        <div className="p-4 space-y-3 overflow-y-auto max-h-[calc(100vh-200px)]">
          {participants.map((participant) => (
            <div key={participant.user_id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-accent">
              <div className="relative">
                <Avatar className="h-8 w-8">
                  <AvatarImage src={participant.user_avatar} />
                  <AvatarFallback>{participant.user_name.charAt(0)}</AvatarFallback>
                </Avatar>
                {participant.is_online && (
                  <div className="absolute -bottom-1 -right-1 h-3 w-3 bg-green-500 border-2 border-background rounded-full"></div>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium truncate">{participant.user_name}</p>
                  {participant.role === 'owner' && <Badge variant="destructive" className="text-xs">Owner</Badge>}
                  {participant.role === 'admin' && <Badge variant="secondary" className="text-xs">Admin</Badge>}
                </div>
                {!participant.is_online && participant.last_seen && (
                  <p className="text-xs text-muted-foreground">
                    Last seen {formatTimestamp(participant.last_seen)}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b bg-card">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold">League Messages</h1>
              <p className="text-sm text-muted-foreground">
                {typingUsers.length > 0 && (
                  <span className="text-primary">
                    {typingUsers.map(u => u.user_name).join(', ')}
                    {typingUsers.length === 1 ? ' is' : ' are'} typing...
                  </span>
                )}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm">
                <Filter className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Pinned Messages */}
        {pinnedMessages.length > 0 && (
          <div className="p-4 bg-muted/50 border-b">
            <div className="flex items-center gap-2 mb-2">
              <Pin className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium">Pinned Messages</span>
            </div>
            <div className="space-y-2">
              {pinnedMessages.slice(0, 3).map((message) => (
                <div key={message.id} className="p-2 bg-background rounded-md border">
                  <div className="flex items-center gap-2 mb-1">
                    <Avatar className="h-5 w-5">
                      <AvatarImage src={message.user_avatar} />
                      <AvatarFallback>{message.user_name.charAt(0)}</AvatarFallback>
                    </Avatar>
                    <span className="text-xs font-medium">{message.user_name}</span>
                    <span className="text-xs text-muted-foreground">
                      {formatTimestamp(message.timestamp)}
                    </span>
                  </div>
                  <p className="text-sm line-clamp-2">{message.content}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {regularMessages.map((message) => (
            <Card key={message.id} className={`${message.is_moderator_message ? 'border-primary/50' : ''}`}>
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <Avatar className="h-8 w-8">
                    <AvatarImage src={message.user_avatar} />
                    <AvatarFallback>{message.user_name.charAt(0)}</AvatarFallback>
                  </Avatar>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-sm">{message.user_name}</span>
                      {getMessageTypeIcon(message.message_type) && (
                        <span className="text-sm">{getMessageTypeIcon(message.message_type)}</span>
                      )}
                      <span className="text-xs text-muted-foreground">
                        {formatTimestamp(message.timestamp)}
                      </span>
                      {message.is_moderator_message && (
                        <Badge variant="outline" className="text-xs">Moderator</Badge>
                      )}
                    </div>

                    <div className="text-sm mb-2 whitespace-pre-wrap break-words">
                      {message.content}
                    </div>

                    {/* Reactions */}
                    {Object.keys(message.reactions).length > 0 && (
                      <div className="flex items-center gap-1 mb-2">
                        {Object.entries(message.reactions).map(([emoji, userIds]) => (
                          <Button
                            key={emoji}
                            variant="outline"
                            size="sm"
                            className="h-6 px-2 text-xs"
                            onClick={() => addReaction(message.id, emoji)}
                          >
                            {emoji} {userIds.length}
                          </Button>
                        ))}
                      </div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex items-center gap-2">
                      <Popover>
                        <PopoverTrigger asChild>
                          <Button variant="ghost" size="sm" className="h-6 px-2">
                            <Heart className="h-3 w-3" />
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-auto p-2">
                          <div className="flex gap-1">
                            {['❤️', '👍', '👎', '😂', '😮', '😢', '😡'].map(emoji => (
                              <Button
                                key={emoji}
                                variant="ghost"
                                size="sm"
                                className="h-8 w-8 p-0"
                                onClick={() => addReaction(message.id, emoji)}
                              >
                                {emoji}
                              </Button>
                            ))}
                          </div>
                        </PopoverContent>
                      </Popover>

                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 px-2"
                        onClick={() => setSelectedThread(message.id)}
                      >
                        <Reply className="h-3 w-3" />
                      </Button>

                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" className="h-6 px-2">
                            <MoreVertical className="h-3 w-3" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent>
                          <DropdownMenuItem onClick={() => pinMessage(message.id)}>
                            <Pin className="h-4 w-4 mr-2" />
                            Pin Message
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => reportMessage(message.id)}>
                            <Flag className="h-4 w-4 mr-2" />
                            Report
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Thread indicator */}
        {selectedThread && (
          <div className="px-4 py-2 bg-muted border-t">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">
                Replying to thread
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedThread(null)}
              >
                Cancel
              </Button>
            </div>
          </div>
        )}

        {/* Message Input */}
        <div className="p-4 border-t bg-card">
          <div className="flex items-end gap-2">
            <div className="flex-1">
              <Input
                value={newMessage}
                onChange={handleInputChange}
                onKeyPress={handleKeyPress}
                placeholder="Type a message..."
                className="min-h-[40px] resize-none"
              />
            </div>
            <Button onClick={sendMessage} disabled={!newMessage.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}