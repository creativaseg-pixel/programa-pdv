import { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform, ScrollView, ActivityIndicator, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Link } from 'expo-router';
import { useAuth } from '../src/auth';
import { theme } from '../src/theme';
import { Ionicons } from '@expo/vector-icons';

export default function Login() {
  const { login } = useAuth();
  const [email, setEmail] = useState('demo@imobiliaria.com');
  const [password, setPassword] = useState('demo1234');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email || !password) { Alert.alert('Erro', 'Preencha email e senha'); return; }
    setLoading(true);
    try { await login(email, password); }
    catch (e: any) { Alert.alert('Falha no login', e.message); }
    finally { setLoading(false); }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={styles.container}>
          <View style={styles.logoBox}>
            <Ionicons name="business" size={48} color={theme.colors.primary} />
            <Text style={styles.brand}>IMOBI</Text>
            <Text style={styles.overline}>SISTEMA DE GESTÃO IMOBILIÁRIA</Text>
          </View>
          <Text style={styles.h1}>Bem-vindo</Text>
          <Text style={styles.subtitle}>Entre para gerenciar sua carteira</Text>

          <Text style={styles.label}>Email</Text>
          <TextInput
            testID="login-email-input"
            style={styles.input}
            value={email}
            onChangeText={setEmail}
            placeholder="seu@email.com"
            placeholderTextColor={theme.colors.textDisabled}
            keyboardType="email-address"
            autoCapitalize="none"
            editable={!loading}
          />

          <Text style={styles.label}>Senha</Text>
          <TextInput
            testID="login-password-input"
            style={styles.input}
            value={password}
            onChangeText={setPassword}
            placeholder="Sua senha"
            placeholderTextColor={theme.colors.textDisabled}
            secureTextEntry
            editable={!loading}
          />

          <TouchableOpacity testID="login-submit-button" style={[styles.btn, loading && styles.btnDisabled]} onPress={handleLogin} disabled={loading}>
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.btnText}>ENTRAR</Text>}
          </TouchableOpacity>

          <Link href="/register" asChild>
            <TouchableOpacity testID="goto-register-link" style={styles.linkBtn}>
              <Text style={styles.linkText}>Não tem conta? <Text style={{ color: theme.colors.primary, fontWeight: '700' }}>Cadastre-se</Text></Text>
            </TouchableOpacity>
          </Link>

          <View style={styles.demoBox}>
            <Text style={styles.demoTitle}>CONTA DEMO</Text>
            <Text style={styles.demoText}>demo@imobiliaria.com</Text>
            <Text style={styles.demoText}>demo1234</Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: theme.colors.bg },
  container: { padding: 24, paddingTop: 40 },
  logoBox: { alignItems: 'center', marginBottom: 40 },
  brand: { fontSize: 28, fontWeight: '800', color: theme.colors.text, marginTop: 8, letterSpacing: -1 },
  overline: { fontSize: 10, color: theme.colors.textSecondary, letterSpacing: 2, marginTop: 4 },
  h1: { fontSize: 32, fontWeight: '800', color: theme.colors.text, letterSpacing: -1 },
  subtitle: { fontSize: 15, color: theme.colors.textSecondary, marginTop: 4, marginBottom: 32 },
  label: { fontSize: 12, color: theme.colors.textSecondary, letterSpacing: 1.5, marginBottom: 8, marginTop: 16, fontWeight: '600' },
  input: { height: 52, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 8, paddingHorizontal: 16, fontSize: 16, color: theme.colors.text, backgroundColor: theme.colors.bg },
  btn: { height: 52, backgroundColor: theme.colors.primary, borderRadius: 8, justifyContent: 'center', alignItems: 'center', marginTop: 32 },
  btnDisabled: { opacity: 0.6 },
  btnText: { color: '#fff', fontSize: 14, fontWeight: '700', letterSpacing: 1.5 },
  linkBtn: { alignItems: 'center', marginTop: 24, padding: 8 },
  linkText: { color: theme.colors.textSecondary, fontSize: 14 },
  demoBox: { marginTop: 32, padding: 16, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 8, backgroundColor: theme.colors.bgSecondary },
  demoTitle: { fontSize: 10, color: theme.colors.textSecondary, letterSpacing: 1.5, fontWeight: '700', marginBottom: 8 },
  demoText: { fontSize: 13, color: theme.colors.text, fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace' },
});
