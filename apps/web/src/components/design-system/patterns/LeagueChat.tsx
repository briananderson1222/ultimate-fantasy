'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Card } from '../primitives/Card';
import { Button } from '../primitives/Button';
import { Avatar } from '../primitives/Avatar';
import { cn } from '../../../lib/utils';

export interface TransactionData {
  type: 'trade' | 'waiver_claim' | 'free_agent_pickup' | 'drop';
  player?: string;
  team?: string;
  fromTeam?: string;
  toTeam?: string;
  fromPlayer?: string;
  toPlayer?: string;
}

export interface ChatMessage {
  id: string;
  userId: string;
  username: string;
  message: string;
  timestamp: Date;
  type: 'message' | 'transaction' | 'announcement';
  transactionData?: TransactionData;
  mentions?: string[];
}

export interface LeagueChatProps {
  messages: ChatMessage[];
  variant?: 'default' | 'compact';
  showComposer?: boolean;
  showTypingIndicator?: boolean;
  showTransactionsOnly?: boolean;
  typingUsers?: string[];
  currentUserId?: string;
  onSendMessage?: (message: string) => void;
  className?: string;
}

const formatTimestamp = (timestamp: Date) => {
  const now = new Date();
  const diffInMs = now.getTime() - timestamp.getTime();
  const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
  const diffInHours = Math.floor(diffInMinutes / 60);
  const diffInDays = Math.floor(diffInHours / 24);

  if (diffInMinutes < 1) return 'Just now';
  if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
  if (diffInHours < 24) return `${diffInHours}h ago`;
  if (diffInDays < 7) return `${diffInDays}d ago`;

  return timestamp.toLocaleDateString();
};

const TransactionMessage: React.FC<{ data: TransactionData }> = ({ data }) => {
  const { type, player, team, fromTeam, toTeam, fromPlayer, toPlayer } = data;

  switch (type) {
    case 'trade':
      return (
        <span>
          Trade completed: <strong>{fromPlayer}</strong> (from {fromTeam}) for{' '}
          <strong>{toPlayer}</strong> (from {toTeam})
        </span>
      );
    case 'waiver_claim':
      return (
        <span>
          <strong>{team}</strong> claimed <strong>{player}</strong> off waivers
        </span>
      );
    case 'free_agent_pickup':
      return (
        <span>
          <strong>{team}</strong> picked up <strong>{player}</strong> as a free agent
        </span>
      );
    case 'drop':
      return (
        <span>
          <strong>{team}</strong> dropped <strong>{player}</strong>
        </span>
      );
    default:
      return <span>Transaction occurred</span>;
  }
};

const MessageBubble: React.FC<{
  message: ChatMessage;
  variant?: 'default' | 'compact';
  isCurrentUser?: boolean;
}> = ({ message, variant = 'default', isCurrentUser = false }) => {
  const { username, message: text, timestamp, type, transactionData, mentions } = message;

  const getMessageTypeStyles = () => {
    switch (type) {
      case 'transaction':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      case 'announcement':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      default:
        return isCurrentUser
          ? 'bg-primary text-white'
          : 'bg-gray-100 text-gray-800';
    }
  };

  const processMessageText = (text: string, mentions?: string[]) => {
    if (!mentions) return text;

    let processedText = text;
    mentions.forEach(mention => {
      const mentionRegex = new RegExp(`@${mention}`, 'g');
      processedText = processedText.replace(
        mentionRegex,
        `<span class="font-semibold text-blue-600">@${mention}</span>`
      );
    });

    return processedText;
  };

  if (variant === 'compact') {
    return (
      <div className="flex items-start gap-2 py-1">
        <Avatar
          fallback={username.charAt(0)}
          size="sm"
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-2">
            <span className="font-medium text-sm">{username}</span>
            <span className="text-xs text-muted-foreground">
              {formatTimestamp(timestamp)}
            </span>
          </div>
          <div className="text-sm">
            {type === 'transaction' && transactionData ? (
              <TransactionMessage data={transactionData} />
            ) : (
              <span
                dangerouslySetInnerHTML={{
                  __html: processMessageText(text, mentions)
                }}
              />
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn(
      'flex gap-3 mb-4',
      isCurrentUser && 'flex-row-reverse'
    )}>
      <Avatar
        fallback={username.charAt(0)}
        size="sm"
      />
      <div className={cn(
        'flex-1 max-w-xs',
        isCurrentUser && 'text-right'
      )}>
        <div className="flex items-baseline gap-2 mb-1">
          <span className="font-medium text-sm">{username}</span>
          <span className="text-xs text-muted-foreground">
            {formatTimestamp(timestamp)}
          </span>
        </div>
        <div className={cn(
          'p-3 rounded-lg text-sm',
          getMessageTypeStyles()
        )}>
          {type === 'transaction' && transactionData ? (
            <TransactionMessage data={transactionData} />
          ) : (
            <span
              dangerouslySetInnerHTML={{
                __html: processMessageText(text, mentions)
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
};

const MessageComposer: React.FC<{
  onSendMessage: (message: string) => void;
}> = ({ onSendMessage }) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim()) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="border-t p-4">
      <div className="flex gap-2">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message..."
          className="flex-1 resize-none border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          rows={1}
        />
        <Button
          type="submit"
          disabled={!message.trim()}
          size="sm"
        >
          Send
        </Button>
      </div>
    </form>
  );
};

const TypingIndicator: React.FC<{ users: string[] }> = ({ users }) => {
  if (users.length === 0) return null;

  const displayText = users.length === 1
    ? `${users[0]} is typing...`
    : users.length === 2
    ? `${users[0]} and ${users[1]} are typing...`
    : `${users[0]} and ${users.length - 1} others are typing...`;

  return (
    <div className="px-4 py-2 text-sm text-muted-foreground italic">
      {displayText}
    </div>
  );
};

export const LeagueChat: React.FC<LeagueChatProps> = ({
  messages,
  variant = 'default',
  showComposer = false,
  showTypingIndicator = false,
  showTransactionsOnly = false,
  typingUsers = [],
  currentUserId,
  onSendMessage,
  className
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  // Filter messages if needed
  const filteredMessages = showTransactionsOnly
    ? messages.filter(msg => msg.type === 'transaction')
    : messages;

  const sortedMessages = [...filteredMessages].sort(
    (a, b) => a.timestamp.getTime() - b.timestamp.getTime()
  );

  return (
    <Card className={cn('flex flex-col h-full', className)}>
      <Card.Header>
        <h3 className="font-semibold">
          {showTransactionsOnly ? 'League Transactions' : 'League Chat'}
        </h3>
      </Card.Header>

      <Card.Content className="flex-1 overflow-hidden">
        <div
          ref={messagesContainerRef}
          className="h-full overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300"
        >
          {sortedMessages.length === 0 ? (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              <div className="text-center">
                <div className="text-4xl mb-2">💬</div>
                <div>No messages yet</div>
                <div className="text-sm">Start the conversation!</div>
              </div>
            </div>
          ) : (
            <div className="space-y-2 p-4">
              {sortedMessages.map((message) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  variant={variant}
                  isCurrentUser={message.userId === currentUserId}
                />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </Card.Content>

      {showTypingIndicator && typingUsers.length > 0 && (
        <TypingIndicator users={typingUsers} />
      )}

      {showComposer && onSendMessage && (
        <MessageComposer onSendMessage={onSendMessage} />
      )}
    </Card>
  );
};