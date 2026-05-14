import { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform, ScrollView, ActivityIndicator, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Link } from 'expo-router';
import { useAuth } from '../src/auth';
import { theme } from '../src/theme';

export default function Register() {
  const { register } = useAuth();
  const [form, setForm] = useState({ full_name: '', email: '', password: '', company: '', creci: '' });
  const [loading, setLoading] = useState(false);

  const update = (k: string, v: string) => setForm({ ...form, [k]: v });

  const handle = async () => {
    if (!form.full_name || !form.email || !form.password) { Alert.alert('Erro', 'Nome, email e senha são obrigatórios'); return; }
    if (form.password.length < 6) { Alert.alert('Erro', 'Senha deve ter no mínimo 6 caracteres'); return; }
    setLoading(true);
    try { await register(form); }
    catch (e: any) { Alert.alert('Erro no cadastro', e.message); }
    finally { setLoading(false); }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={styles.container}>
          <Text style={styles.h1}>Criar Conta</Text>
          <Text style={styles.subtitle}>Comece a gerenciar sua imobiliária</Text>

          <Text style={styles.label}>Nome Completo *</Text>
          <TextInput testID="reg-name" style={styles.input} value={form.full_name} onChangeText={v => update('full_name', v)} placeholder="Seu nome" placeholderTextColor={theme.colors.textDisabled} />

          <Text style={styles.label}>Email *</Text>
          <TextInput testID="reg-email" style={styles.input} value={form.email} onChangeText={v => update('email', v)} placeholder="seu@email.com" placeholderTextColor={theme.colors.textDisabled} keyboardType="email-address" autoCapitalize="none" />

          <Text style={styles.label}>Senha * (mín. 6)</Text>
          <TextInput testID="reg-password" style={styles.input} value={form.password} onChangeText={v => update('password', v)} placeholder="Senha" placeholderTextColor={theme.colors.textDisabled} secureTextEntry />

          <Text style={styles.label}>Imobiliária / Empresa</Text>
          <TextInput testID="reg-company" style={styles.input} value={form.company} onChangeText={v => update('company', v)} placeholder="Opcional" placeholderTextColor={theme.colors.textDisabled} />

          <Text style={styles.label}>CRECI</Text>
          <TextInput testID="reg-creci" style={styles.input} value={form.creci} onChangeText={v => update('creci', v)} placeholder="Ex: 12345-F" placeholderTextColor={theme.colors.textDisabled} />

          <TouchableOpacity testID="reg-submit" style={[styles.btn, loading && { opacity: 0.6 }]} onPress={handle} disabled={loading}>
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.btnText}>CRIAR CONTA</Text>}
          </TouchableOpacity>

          <Link href="/login" asChild>
            <TouchableOpacity style={{ alignItems: 'center', marginTop: 24, padding: 8 }}>
              <Text style={{ color: theme.colors.textSecondary }}>Já tem conta? <Text style={{ color: theme.colors.primary, fontWeight: '700' }}>Entrar</Text></Text>
            </TouchableOpacity>
          </Link>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: theme.colors.bg },
  container: { padding: 24, paddingTop: 40 },
  h1: { fontSize: 32, fontWeight: '800', color: theme.colors.text, letterSpacing: -1 },
  subtitle: { fontSize: 15, color: theme.colors.textSecondary, marginTop: 4, marginBottom: 16 },
  label: { fontSize: 12, color: theme.colors.textSecondary, letterSpacing: 1.5, marginBottom: 8, marginTop: 16, fontWeight: '600' },
  input: { height: 52, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 8, paddingHorizontal: 16, fontSize: 16, color: theme.colors.text },
  btn: { height: 52, backgroundColor: theme.colors.primary, borderRadius: 8, justifyContent: 'center', alignItems: 'center', marginTop: 32 },
  btnText: { color: '#fff', fontSize: 14, fontWeight: '700', letterSpacing: 1.5 },
});
