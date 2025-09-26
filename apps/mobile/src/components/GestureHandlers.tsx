import React, { useRef, useCallback, useMemo } from "react";
import {
  View,
  Animated,
  PanResponder,
  Dimensions,
  StyleSheet,
} from "react-native";
import {
  PanGestureHandler,
  TapGestureHandler,
  PinchGestureHandler,
  State,
} from "react-native-gesture-handler";

const { width: screenWidth, height: screenHeight } = Dimensions.get("window");

export interface SwipeGestureProps {
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
  onSwipeDown?: () => void;
  threshold?: number;
  velocityThreshold?: number;
  children: React.ReactNode;
}

export const SwipeGestureHandler: React.FC<SwipeGestureProps> = ({
  onSwipeLeft,
  onSwipeRight,
  onSwipeUp,
  onSwipeDown,
  threshold = 50,
  velocityThreshold = 500,
  children,
}) => {
  const panResponder = useMemo(
    () =>
      PanResponder.create({
        onMoveShouldSetPanResponder: (_, gestureState) => {
          return (
            Math.abs(gestureState.dx) > 10 || Math.abs(gestureState.dy) > 10
          );
        },

        onPanResponderRelease: (_, gestureState) => {
          const { dx, dy, vx, vy } = gestureState;

          if (Math.abs(dx) > Math.abs(dy)) {
            if (dx > threshold || vx > velocityThreshold) {
              onSwipeRight?.();
            } else if (dx < -threshold || vx < -velocityThreshold) {
              onSwipeLeft?.();
            }
          } else {
            if (dy > threshold || vy > velocityThreshold) {
              onSwipeDown?.();
            } else if (dy < -threshold || vy < -velocityThreshold) {
              onSwipeUp?.();
            }
          }
        },
      }),
    [
      onSwipeLeft,
      onSwipeRight,
      onSwipeUp,
      onSwipeDown,
      threshold,
      velocityThreshold,
    ],
  );

  return (
    <View {...panResponder.panHandlers} style={{ flex: 1 }}>
      {children}
    </View>
  );
};

export interface DragDropProps {
  onDragStart?: (id: string) => void;
  onDragMove?: (id: string, x: number, y: number) => void;
  onDragEnd?: (id: string, x: number, y: number) => void;
  onDrop?: (draggedId: string, targetId: string) => void;
  dragId: string;
  dropTargetId?: string;
  disabled?: boolean;
  children: React.ReactNode;
}

export const DragDropHandler: React.FC<DragDropProps> = ({
  onDragStart,
  onDragMove,
  onDragEnd,
  onDrop,
  dragId,
  dropTargetId,
  disabled = false,
  children,
}) => {
  const translateX = useRef(new Animated.Value(0)).current;
  const translateY = useRef(new Animated.Value(0)).current;
  const scale = useRef(new Animated.Value(1)).current;
  const isDragging = useRef(false);

  const panResponder = useMemo(
    () =>
      PanResponder.create({
        onStartShouldSetPanResponder: () => !disabled,
        onMoveShouldSetPanResponder: () => !disabled,

        onPanResponderGrant: () => {
          isDragging.current = true;
          onDragStart?.(dragId);

          Animated.spring(scale, {
            toValue: 1.1,
            useNativeDriver: true,
          }).start();
        },

        onPanResponderMove: (_, gestureState) => {
          translateX.setValue(gestureState.dx);
          translateY.setValue(gestureState.dy);
          onDragMove?.(dragId, gestureState.moveX, gestureState.moveY);
        },

        onPanResponderRelease: (_, gestureState) => {
          isDragging.current = false;
          const finalX = gestureState.moveX;
          const finalY = gestureState.moveY;

          onDragEnd?.(dragId, finalX, finalY);

          if (dropTargetId) {
            onDrop?.(dragId, dropTargetId);
          }

          Animated.parallel([
            Animated.spring(translateX, { toValue: 0, useNativeDriver: true }),
            Animated.spring(translateY, { toValue: 0, useNativeDriver: true }),
            Animated.spring(scale, { toValue: 1, useNativeDriver: true }),
          ]).start();
        },
      }),
    [
      disabled,
      dragId,
      dropTargetId,
      onDragStart,
      onDragMove,
      onDragEnd,
      onDrop,
    ],
  );

  return (
    <Animated.View
      {...panResponder.panHandlers}
      style={{
        transform: [{ translateX }, { translateY }, { scale }],
      }}
    >
      {children}
    </Animated.View>
  );
};

export interface PullToRefreshProps {
  onRefresh: () => Promise<void>;
  refreshThreshold?: number;
  children: React.ReactNode;
}

export const PullToRefreshHandler: React.FC<PullToRefreshProps> = ({
  onRefresh,
  refreshThreshold = 100,
  children,
}) => {
  const translateY = useRef(new Animated.Value(0)).current;
  const isRefreshing = useRef(false);

  const panResponder = useMemo(
    () =>
      PanResponder.create({
        onMoveShouldSetPanResponder: (_, gestureState) => {
          return (
            gestureState.dy > 0 &&
            Math.abs(gestureState.dx) < Math.abs(gestureState.dy)
          );
        },

        onPanResponderMove: (_, gestureState) => {
          if (gestureState.dy > 0) {
            translateY.setValue(
              Math.min(gestureState.dy, refreshThreshold * 1.5),
            );
          }
        },

        onPanResponderRelease: async (_, gestureState) => {
          if (gestureState.dy > refreshThreshold && !isRefreshing.current) {
            isRefreshing.current = true;

            try {
              await onRefresh();
            } finally {
              isRefreshing.current = false;
              Animated.spring(translateY, {
                toValue: 0,
                useNativeDriver: true,
              }).start();
            }
          } else {
            Animated.spring(translateY, {
              toValue: 0,
              useNativeDriver: true,
            }).start();
          }
        },
      }),
    [onRefresh, refreshThreshold],
  );

  return (
    <Animated.View
      {...panResponder.panHandlers}
      style={{
        flex: 1,
        transform: [{ translateY }],
      }}
    >
      {children}
    </Animated.View>
  );
};

export interface DoubleTapProps {
  onDoubleTap: () => void;
  delay?: number;
  children: React.ReactNode;
}

export const DoubleTapHandler: React.FC<DoubleTapProps> = ({
  onDoubleTap,
  delay = 300,
  children,
}) => {
  const doubleTapRef = useRef<TapGestureHandler>(null);

  const onDoubleTapEvent = useCallback(
    (event: any) => {
      if (event.nativeEvent.state === State.ACTIVE) {
        onDoubleTap();
      }
    },
    [onDoubleTap],
  );

  return (
    <TapGestureHandler
      ref={doubleTapRef}
      onHandlerStateChange={onDoubleTapEvent}
      numberOfTaps={2}
      maxDelayMs={delay}
    >
      <View style={{ flex: 1 }}>{children}</View>
    </TapGestureHandler>
  );
};

export interface PinchZoomProps {
  onZoomChange?: (scale: number) => void;
  minScale?: number;
  maxScale?: number;
  children: React.ReactNode;
}

export const PinchZoomHandler: React.FC<PinchZoomProps> = ({
  onZoomChange,
  minScale = 0.5,
  maxScale = 3,
  children,
}) => {
  const scale = useRef(new Animated.Value(1)).current;
  const lastScale = useRef(1);

  const onPinchEvent = useCallback(
    (event: any) => {
      const newScale = Math.min(
        Math.max(lastScale.current * event.nativeEvent.scale, minScale),
        maxScale,
      );
      scale.setValue(newScale);
      onZoomChange?.(newScale);
    },
    [scale, minScale, maxScale, onZoomChange],
  );

  const onPinchStateChange = useCallback((event: any) => {
    if (event.nativeEvent.oldState === State.ACTIVE) {
      lastScale.current *= event.nativeEvent.scale;
    }
  }, []);

  return (
    <PinchGestureHandler
      onGestureEvent={onPinchEvent}
      onHandlerStateChange={onPinchStateChange}
    >
      <Animated.View style={{ transform: [{ scale }] }}>
        {children}
      </Animated.View>
    </PinchGestureHandler>
  );
};

export interface LongPressProps {
  onLongPress: () => void;
  duration?: number;
  children: React.ReactNode;
}

export const LongPressHandler: React.FC<LongPressProps> = ({
  onLongPress,
  duration = 500,
  children,
}) => {
  const scale = useRef(new Animated.Value(1)).current;

  const panResponder = useMemo(
    () =>
      PanResponder.create({
        onStartShouldSetPanResponder: () => true,

        onPanResponderGrant: () => {
          Animated.spring(scale, {
            toValue: 0.95,
            useNativeDriver: true,
          }).start();

          setTimeout(() => {
            onLongPress();
          }, duration);
        },

        onPanResponderRelease: () => {
          Animated.spring(scale, {
            toValue: 1,
            useNativeDriver: true,
          }).start();
        },
      }),
    [onLongPress, duration, scale],
  );

  return (
    <Animated.View
      {...panResponder.panHandlers}
      style={{ transform: [{ scale }] }}
    >
      {children}
    </Animated.View>
  );
};

export interface SlideActionsProps {
  leftActions?: Array<{
    text: string;
    color: string;
    onPress: () => void;
  }>;
  rightActions?: Array<{
    text: string;
    color: string;
    onPress: () => void;
  }>;
  actionWidth?: number;
  children: React.ReactNode;
}

export const SlideActionsHandler: React.FC<SlideActionsProps> = ({
  leftActions = [],
  rightActions = [],
  actionWidth = 80,
  children,
}) => {
  const translateX = useRef(new Animated.Value(0)).current;
  const maxLeftTranslate = leftActions.length * actionWidth;
  const maxRightTranslate = rightActions.length * actionWidth;

  const panResponder = useMemo(
    () =>
      PanResponder.create({
        onMoveShouldSetPanResponder: (_, gestureState) => {
          return (
            Math.abs(gestureState.dx) > Math.abs(gestureState.dy) &&
            Math.abs(gestureState.dx) > 10
          );
        },

        onPanResponderMove: (_, gestureState) => {
          const newValue = Math.max(
            -maxRightTranslate,
            Math.min(maxLeftTranslate, gestureState.dx),
          );
          translateX.setValue(newValue);
        },

        onPanResponderRelease: (_, gestureState) => {
          const threshold = 50;
          let targetValue = 0;

          if (gestureState.dx > threshold && leftActions.length > 0) {
            targetValue = maxLeftTranslate;
          } else if (gestureState.dx < -threshold && rightActions.length > 0) {
            targetValue = -maxRightTranslate;
          }

          Animated.spring(translateX, {
            toValue: targetValue,
            useNativeDriver: true,
          }).start();
        },
      }),
    [
      maxLeftTranslate,
      maxRightTranslate,
      leftActions.length,
      rightActions.length,
    ],
  );

  const renderActions = (actions: any[], isLeft: boolean) => {
    return actions.map((action, index) => (
      <Animated.View
        key={index}
        style={[
          styles.actionButton,
          {
            backgroundColor: action.color,
            width: actionWidth,
            [isLeft ? "left" : "right"]: index * actionWidth,
          },
        ]}
      >
        <Animated.Text style={styles.actionText} onPress={action.onPress}>
          {action.text}
        </Animated.Text>
      </Animated.View>
    ));
  };

  return (
    <View style={styles.container}>
      {leftActions.length > 0 && (
        <View style={[styles.actionsContainer, styles.leftActions]}>
          {renderActions(leftActions, true)}
        </View>
      )}

      {rightActions.length > 0 && (
        <View style={[styles.actionsContainer, styles.rightActions]}>
          {renderActions(rightActions, false)}
        </View>
      )}

      <Animated.View
        {...panResponder.panHandlers}
        style={[styles.content, { transform: [{ translateX }] }]}
      >
        {children}
      </Animated.View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    overflow: "hidden",
  },
  actionsContainer: {
    position: "absolute",
    top: 0,
    bottom: 0,
    flexDirection: "row",
  },
  leftActions: {
    left: 0,
  },
  rightActions: {
    right: 0,
  },
  actionButton: {
    position: "absolute",
    top: 0,
    bottom: 0,
    justifyContent: "center",
    alignItems: "center",
  },
  actionText: {
    color: "white",
    fontWeight: "bold",
    fontSize: 14,
  },
  content: {
    flex: 1,
    backgroundColor: "white",
  },
});

export interface MultiTouchProps {
  onSingleTap?: () => void;
  onDoubleTap?: () => void;
  onTripleTap?: () => void;
  onPinch?: (scale: number) => void;
  onRotate?: (rotation: number) => void;
  children: React.ReactNode;
}

export const MultiTouchHandler: React.FC<MultiTouchProps> = ({
  onSingleTap,
  onDoubleTap,
  onTripleTap,
  onPinch,
  onRotate,
  children,
}) => {
  const singleTapRef = useRef<TapGestureHandler>(null);
  const doubleTapRef = useRef<TapGestureHandler>(null);
  const tripleTapRef = useRef<TapGestureHandler>(null);

  return (
    <TapGestureHandler
      ref={tripleTapRef}
      numberOfTaps={3}
      onHandlerStateChange={(event) => {
        if (event.nativeEvent.state === State.ACTIVE) {
          onTripleTap?.();
        }
      }}
    >
      <TapGestureHandler
        ref={doubleTapRef}
        numberOfTaps={2}
        waitFor={tripleTapRef}
        onHandlerStateChange={(event) => {
          if (event.nativeEvent.state === State.ACTIVE) {
            onDoubleTap?.();
          }
        }}
      >
        <TapGestureHandler
          ref={singleTapRef}
          waitFor={doubleTapRef}
          onHandlerStateChange={(event) => {
            if (event.nativeEvent.state === State.ACTIVE) {
              onSingleTap?.();
            }
          }}
        >
          <PinchGestureHandler
            onGestureEvent={(event) => {
              onPinch?.(event.nativeEvent.scale);
            }}
          >
            <View style={{ flex: 1 }}>{children}</View>
          </PinchGestureHandler>
        </TapGestureHandler>
      </TapGestureHandler>
    </TapGestureHandler>
  );
};

export {
  SwipeGestureHandler as Swipe,
  DragDropHandler as DragDrop,
  PullToRefreshHandler as PullToRefresh,
  DoubleTapHandler as DoubleTap,
  PinchZoomHandler as PinchZoom,
  LongPressHandler as LongPress,
  SlideActionsHandler as SlideActions,
  MultiTouchHandler as MultiTouch,
};
