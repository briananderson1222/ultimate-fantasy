import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { dashboardUtils, DEFAULT_WIDGETS, WidgetKey } from '@ultimate-fantasy/shared-logic';

export default function DashboardScreen() {
  const [order, setOrder] = useState<WidgetKey[]>(DEFAULT_WIDGETS);

  useEffect(() => {
    setOrder(dashboardUtils.loadLayout());
  }, []);

  const renderWidget = (key: WidgetKey) => {
    const getWidgetContent = () => {
      switch (key) {
        case 'myLeagues':
          return 'Quick access to your leagues.';
        case 'upcoming':
          return 'Upcoming matchups and deadlines.';
        case 'scoreboard':
          return 'Recent scores at a glance.';
        case 'waivers':
          return 'Waiver bids and activity.';
        case 'tips':
          return 'Helpful tips and onboarding links.';
        default:
          return 'Widget content';
      }
    };

    const getWidgetTitle = () => {
      switch (key) {
        case 'myLeagues':
          return 'My Leagues';
        case 'upcoming':
          return 'Upcoming';
        case 'scoreboard':
          return 'Scoreboard';
        case 'waivers':
          return 'Waivers';
        case 'tips':
          return 'Tips';
        default:
          return key;
      }
    };

    return (
      <View key={key} style={styles.widget}>
        <View style={styles.widgetHeader}>
          <Text style={styles.widgetTitle}>{getWidgetTitle()}</Text>
        </View>
        <Text style={styles.widgetContent}>{getWidgetContent()}</Text>
      </View>
    );
  };

  const resetLayout = () => {
    setOrder(DEFAULT_WIDGETS);
  };

  const saveLayout = () => {
    dashboardUtils.saveLayout(order);
    // Could add a toast notification here
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Dashboard</Text>
        <View style={styles.headerButtons}>
          <TouchableOpacity style={styles.button} onPress={saveLayout}>
            <Text style={styles.buttonText}>Save</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.button, styles.secondaryButton]} onPress={resetLayout}>
            <Text style={[styles.buttonText, styles.secondaryButtonText]}>Reset</Text>
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContainer}>
        {order.map((key) => renderWidget(key))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1e293b',
  },
  headerButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  button: {
    backgroundColor: '#3b82f6',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 6,
  },
  secondaryButton: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#d1d5db',
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  secondaryButtonText: {
    color: '#374151',
  },
  scrollContainer: {
    padding: 16,
    gap: 16,
  },
  widget: {
    backgroundColor: '#ffffff',
    borderRadius: 8,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  widgetHeader: {
    marginBottom: 8,
  },
  widgetTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
  },
  widgetContent: {
    fontSize: 14,
    color: '#64748b',
    lineHeight: 20,
  },
});