import React from 'react';
import { render } from '@testing-library/react-native';
import HomeScreen from './HomeScreen';

describe('HomeScreen', () => {
  it('renders correctly', () => {
    const navigation = {
      navigate: jest.fn(),
      goBack: jest.fn(),
    } as any;

    const { getByText } = render(<HomeScreen navigation={navigation} />);
    expect(getByText('Ultimate Fantasy')).toBeDefined();
  });
});
