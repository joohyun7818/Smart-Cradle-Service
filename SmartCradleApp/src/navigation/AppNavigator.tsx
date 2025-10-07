import React from 'react';
import { Text } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { logScreenView } from '../services/analytics'; // GA 추적 함수 임포트
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useSelector } from 'react-redux';
import { RootState } from '../store';

// Screens
import LoginScreen from '../screens/LoginScreen';
import RegisterScreen from '../screens/RegisterScreen';
import RegisterCradleScreen from '../screens/RegisterCradleScreen';
import AgentSelectionScreen from '../screens/AgentSelectionScreen';
import DashboardScreen from '../screens/DashboardScreen';
import AlertsScreen from '../screens/AlertsScreen';
import SettingsScreen from '../screens/SettingsScreen';
import HistoryScreen from '../screens/HistoryScreen';
import AlertDetailScreen from '../screens/AlertDetailScreen';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

// 메인 탭 네비게이터
const MainTabs = () => {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: '#4A90E2',
        tabBarInactiveTintColor: '#999',
      }}
    >
      <Tab.Screen
        name="Dashboard"
        component={DashboardScreen}
        options={{
          tabBarLabel: '대시보드',
          tabBarIcon: ({ color, size }) => (
            <TabIcon name="📊" color={color} size={size} />
          ),
        }}
      />
      <Tab.Screen
        name="Alerts"
        component={AlertsScreen}
        options={{
          tabBarLabel: '알림',
          tabBarIcon: ({ color, size }) => (
            <TabIcon name="🔔" color={color} size={size} />
          ),
        }}
      />
      <Tab.Screen
        name="History"
        component={HistoryScreen}
        options={{
          tabBarLabel: '히스토리',
          tabBarIcon: ({ color, size }) => (
            <TabIcon name="📈" color={color} size={size} />
          ),
        }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          tabBarLabel: '설정',
          tabBarIcon: ({ color, size }) => (
            <TabIcon name="⚙️" color={color} size={size} />
          ),
        }}
      />
      <Tab.Screen
        name="AgentSelection"
        component={AgentSelectionScreen}
        options={{
          tabBarLabel: '요람 선택',
          tabBarIcon: ({ color, size }) => (
            <TabIcon name="🍼" color={color} size={size} />
          ),
        }}
      />
    </Tab.Navigator>
  );
};

// 간단한 아이콘 컴포넌트
const TabIcon = ({ name, size }: { name: string; color: string; size: number }) => {
  return <Text style={{ fontSize: size }}>{name}</Text>;
};

// 루트 네비게이터
const AppNavigator = () => {
  const { isAuthenticated } = useSelector((state: RootState) => state.auth);

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {!isAuthenticated ? (
          <>
            <Stack.Screen name="Login" component={LoginScreen} />
            <Stack.Screen name="Register" component={RegisterScreen} />
          </>
        ) : (
          <>
            <Stack.Screen name="Main" component={MainTabs} />
            <Stack.Screen 
              name="RegisterCradle" 
              component={RegisterCradleScreen}
              options={{ headerShown: true, title: '요람 등록' }}
            />
            <Stack.Screen 
              name="AlertDetail" 
              component={AlertDetailScreen}
              options={{ headerShown: false }}
            />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default AppNavigator;
