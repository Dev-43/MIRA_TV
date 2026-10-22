import React from "react";
import {
  Pressable,
  Text,
  View,
  StyleSheet,
  PressableProps,
  ViewStyle,
} from "react-native";
import { scaledPixels } from "../hooks/useScale";
import { SpatialNavigationFocusableView } from "react-tv-space-navigation";
import { colors } from "../theme/colors";

import { reportFocus } from "../../../../mira/reportFocus";

interface CustomPressableProps extends PressableProps {
  text: string;
  onSelect: () => void;
  style?: ViewStyle;
  screen?: string;
  elementId?: string;
  isFocusable?: boolean;
}

const FocusablePressable = React.memo(({
  text,
  onSelect,
  style,
  screen,
  elementId,
  isFocusable = true,
  ...props
}: CustomPressableProps) => {
  const containerRef = React.useRef<View>(null);

  if (!isFocusable) {
    return (
      <View ref={containerRef}>
        <Pressable
          {...props}
          style={[styles.watchButton, style]}
          onPress={onSelect}
        >
          <Text style={styles.watchButtonText}>{text}</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <SpatialNavigationFocusableView
      onSelect={onSelect}
      onFocus={() => {
        if (screen && elementId) {
          if (containerRef.current?.measureInWindow) {
            containerRef.current.measureInWindow((x, y, w, h) => {
              if (typeof x === 'number' && !isNaN(x)) {
                reportFocus(screen, elementId, { x, y, w, h });
              } else {
                reportFocus(screen, elementId);
              }
            });
          } else {
            reportFocus(screen, elementId);
          }
        }
      }}
    >
      {({ isFocused }) => (
        <View ref={containerRef}>
          <Pressable
            {...props}
            style={[
              styles.watchButton,
              isFocused && styles.watchButtonFocused,
              style,
            ]}
            onPress={onSelect}
          >
            <Text
              style={[
                styles.watchButtonText,
                isFocused && styles.watchButtonTextFocused,
              ]}
            >
              {text}
            </Text>
          </Pressable>
        </View>
      )}
    </SpatialNavigationFocusableView>
  );
});

const styles = StyleSheet.create({
  watchButton: {
    backgroundColor: colors.cardElevated,
    paddingVertical: scaledPixels(20),
    paddingHorizontal: scaledPixels(40),
    borderRadius: scaledPixels(8),
    borderWidth: scaledPixels(3),
    borderColor: 'transparent',
    alignItems: "center",
    justifyContent: "center",
    alignSelf: "flex-start",
    minWidth: scaledPixels(200),
    minHeight: scaledPixels(60),
    maxWidth: '90%',
  },
  watchButtonFocused: {
    backgroundColor: colors.focusBackground,
    borderColor: colors.focusBackground,
    transform: [{ scale: 1.05 }],
    // Shadow for depth
    shadowColor: colors.focus,
    shadowOffset: {
      width: 0,
      height: 0,
    },
    shadowOpacity: 0.6,
    shadowRadius: scaledPixels(12),
    elevation: 8,
  },
  watchButtonText: {
    color: colors.text,
    fontSize: scaledPixels(24),
    fontWeight: "bold",
    textAlign: "center",
  },
  watchButtonTextFocused: {
    color: colors.textOnPrimary,
    fontSize: scaledPixels(24),
    fontWeight: "bold",
  },
});

export default FocusablePressable;
