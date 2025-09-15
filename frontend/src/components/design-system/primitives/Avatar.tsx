'use client';

import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../../lib/utils';

const avatarVariants = cva(
  'relative flex shrink-0 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-700',
  {
    variants: {
      size: {
        sm: 'h-6 w-6',
        md: 'h-8 w-8',
        lg: 'h-10 w-10',
        xl: 'h-12 w-12',
        '2xl': 'h-16 w-16',
      },
    },
    defaultVariants: {
      size: 'md',
    },
  }
);

const avatarImageVariants = cva(
  'aspect-square h-full w-full object-cover',
  {
    variants: {
      size: {
        sm: '',
        md: '',
        lg: '',
        xl: '',
        '2xl': '',
      },
    },
  }
);

const avatarFallbackVariants = cva(
  'flex h-full w-full items-center justify-center rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 font-medium',
  {
    variants: {
      size: {
        sm: 'text-xs',
        md: 'text-sm',
        lg: 'text-sm',
        xl: 'text-base',
        '2xl': 'text-lg',
      },
    },
    defaultVariants: {
      size: 'md',
    },
  }
);

export interface AvatarProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof avatarVariants> {
  src?: string;
  alt?: string;
  fallback?: string;
  teamLogo?: boolean;
}

const Avatar = React.forwardRef<HTMLDivElement, AvatarProps>(
  ({
    className,
    size,
    src,
    alt,
    fallback,
    teamLogo = false,
    ...props
  }, ref) => {
    const [imageError, setImageError] = React.useState(false);
    const [imageLoaded, setImageLoaded] = React.useState(false);

    const handleImageError = () => {
      setImageError(true);
    };

    const handleImageLoad = () => {
      setImageLoaded(true);
      setImageError(false);
    };

    // Generate initials from alt text or fallback
    const getInitials = (text?: string): string => {
      if (!text) return '?';

      return text
        .split(' ')
        .map(word => word.charAt(0).toUpperCase())
        .slice(0, 2)
        .join('');
    };

    const initials = getInitials(alt || fallback);

    // Team logos get different styling
    const avatarClassName = cn(
      avatarVariants({ size }),
      teamLogo && 'rounded-md bg-white dark:bg-white border border-gray-200',
      className
    );

    return (
      <div
        ref={ref}
        className={avatarClassName}
        {...props}
      >
        {src && !imageError && (
          <img
            src={src}
            alt={alt || 'Avatar'}
            className={cn(
              avatarImageVariants({ size }),
              teamLogo && 'rounded-sm p-1',
              !imageLoaded && 'opacity-0'
            )}
            onError={handleImageError}
            onLoad={handleImageLoad}
            loading="lazy"
          />
        )}

        {/* Show fallback when no image, image failed, or image is loading */}
        {(!src || imageError || !imageLoaded) && (
          <div
            className={cn(
              avatarFallbackVariants({ size }),
              teamLogo && 'bg-gray-200 dark:bg-gray-200 text-gray-700 rounded-sm'
            )}
          >
            {teamLogo ? (
              <span className="text-xs font-bold">
                {(alt || fallback || '?').substring(0, 3).toUpperCase()}
              </span>
            ) : (
              initials
            )}
          </div>
        )}

        {/* Loading state indicator */}
        {src && !imageLoaded && !imageError && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-100 dark:bg-gray-700 animate-pulse">
            <div className="w-1/3 h-1/3 bg-gray-300 dark:bg-gray-600 rounded-full" />
          </div>
        )}
      </div>
    );
  }
);

Avatar.displayName = 'Avatar';

// Avatar Group component for displaying multiple avatars
export interface AvatarGroupProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  max?: number;
  spacing?: 'tight' | 'normal' | 'loose';
}

const AvatarGroup = React.forwardRef<HTMLDivElement, AvatarGroupProps>(
  ({ className, children, max = 5, spacing = 'normal', ...props }, ref) => {
    const avatars = React.Children.toArray(children);
    const visibleAvatars = avatars.slice(0, max);
    const extraCount = avatars.length - max;

    const spacingClasses = {
      tight: '-space-x-1',
      normal: '-space-x-2',
      loose: '-space-x-1',
    };

    return (
      <div
        ref={ref}
        className={cn('flex items-center', spacingClasses[spacing], className)}
        {...props}
      >
        {visibleAvatars.map((avatar, index) => (
          <div
            key={index}
            className="ring-2 ring-white dark:ring-gray-800"
            style={{ zIndex: visibleAvatars.length - index }}
          >
            {avatar}
          </div>
        ))}

        {extraCount > 0 && (
          <div
            className="ring-2 ring-white dark:ring-gray-800"
            style={{ zIndex: 0 }}
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-100 dark:bg-gray-700 text-xs font-medium text-gray-600 dark:text-gray-300">
              +{extraCount}
            </div>
          </div>
        )}
      </div>
    );
  }
);

AvatarGroup.displayName = 'AvatarGroup';

export { Avatar, AvatarGroup };