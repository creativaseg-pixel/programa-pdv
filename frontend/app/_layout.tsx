import { Stack, useRouter, useSegments } from 'expo-router';
import { AuthProvider, useAuth } from '../src/auth';
import { useEffect } from 'react';
import { View, ActivityIndicator } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { theme } from '../src/theme';

function RootNav() {
  const { user, loading } = useAuth();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    const inAuth = segments[0] === 'login' || segments[0] === 'register' || !segments[0];
    if (!user && segments[0] === '(tabs)') {
      router.replace('/login');
    } else if (user && (segments[0] === 'login' || segments[0] === 'register' || !segments[0])) {
      router.replace('/(tabs)');
    }
  }, [user, loading, segments]);

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: theme.colors.bg }}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
      </View>
    );
  }

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="index" />
      <Stack.Screen name="login" />
      <Stack.Screen name="register" />
      <Stack.Screen name="(tabs)" />
      <Stack.Screen name="property-form" options={{ presentation: 'modal' }} />
      <Stack.Screen name="client-form" options={{ presentation: 'modal' }} />
      <Stack.Screen name="contract-form" options={{ presentation: 'modal' }} />
      <Stack.Screen name="receipt-form" options={{ presentation: 'modal' }} />
      <Stack.Screen name="contract-view" options={{ presentation: 'modal' }} />
      <Stack.Screen name="receipt-view" options={{ presentation: 'modal' }} />
    </Stack>
  );
}

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <RootNav />
      </AuthProvider>
    </SafeAreaProvider>
  );
}
