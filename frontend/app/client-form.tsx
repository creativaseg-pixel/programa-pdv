import { useState, useEffect } from 'react';
import { View, Text, ScrollView, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform, Alert, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../src/api';
import { theme } from '../src/theme';

const TYPES = [
  { key: 'proprietario', label: 'Proprietário' },
  { key: 'inquilino', label: 'Inquilino' },
  { key: 'comprador', label: 'Comprador' },
];

export default function ClientForm() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id?: string }>();
  const [form, setForm] = useState<any>({
    name: '', cpf_cnpj: '', email: '', phone: '', type: 'inquilino', address: '', notes: '',
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (id) (async () => {
      const c = await api.get(`/clients/${id}`);
      setForm(c);
    })();
  }, [id]);

  const update = (k: string, v: any) => setForm({ ...form, [k]: v });

  const save = async () => {
    if (!form.name || !form.cpf_cnpj || !form.phone) { Alert.alert('Erro', 'Nome, CPF/CNPJ e telefone são obrigatórios'); return; }
    setLoading(true);
    try {
      if (id) await api.put(`/clients/${id}`, form);
      else await api.post('/clients', form);
      router.back();
    } catch (e: any) { Alert.alert('Erro', e.message); }
    finally { setLoading(false); }
  };

  return (
    <SafeAreaView style={s.safe}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Ionicons name="close" size={26} color={theme.colors.text} /></TouchableOpacity>
        <Text style={s.title}>{id ? 'Editar' : 'Novo'} Cliente</Text>
        <View style={{ width: 26 }} />
      </View>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={{ padding: 20 }}>
          <Text style={s.label}>Tipo</Text>
          <View style={s.segRow}>
            {TYPES.map(t => (
              <TouchableOpacity key={t.key} style={[s.seg, form.type === t.key && s.segActive]} onPress={() => update('type', t.key)}>
                <Text style={[s.segText, form.type === t.key && s.segTextActive]}>{t.label}</Text>
              </TouchableOpacity>
            ))}
          </View>

          <Field label="Nome completo *" value={form.name} onChange={(v: string) => update('name', v)} />
          <Field label="CPF/CNPJ *" value={form.cpf_cnpj} onChange={(v: string) => update('cpf_cnpj', v)} placeholder="000.000.000-00" />
          <Field label="Telefone *" value={form.phone} onChange={(v: string) => update('phone', v)} keyboardType="phone-pad" placeholder="(11) 99999-9999" />
          <Field label="Email" value={form.email} onChange={(v: string) => update('email', v)} keyboardType="email-address" />
          <Field label="Endereço" value={form.address} onChange={(v: string) => update('address', v)} />
          <Field label="Observações" value={form.notes} onChange={(v: string) => update('notes', v)} multiline />

          <TouchableOpacity testID="client-save-btn" style={s.btn} onPress={save} disabled={loading}>
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={s.btnText}>{id ? 'ATUALIZAR' : 'SALVAR'}</Text>}
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function Field({ label, value, onChange, placeholder, keyboardType, multiline }: any) {
  return (
    <View>
      <Text style={s.label}>{label}</Text>
      <TextInput style={[s.input, multiline && { height: 80, textAlignVertical: 'top' }]} value={value} onChangeText={onChange} placeholder={placeholder} placeholderTextColor={theme.colors.textDisabled} keyboardType={keyboardType} multiline={multiline} />
    </View>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: theme.colors.bg },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 20, borderBottomWidth: 1, borderBottomColor: theme.colors.border },
  title: { fontSize: 18, fontWeight: '700', color: theme.colors.text },
  label: { fontSize: 11, color: theme.colors.textSecondary, letterSpacing: 1.5, marginBottom: 8, marginTop: 16, fontWeight: '600' },
  input: { height: 48, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 8, paddingHorizontal: 14, fontSize: 15, color: theme.colors.text },
  segRow: { flexDirection: 'row', gap: 6 },
  seg: { flex: 1, paddingVertical: 12, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 6, backgroundColor: theme.colors.bg, alignItems: 'center' },
  segActive: { backgroundColor: theme.colors.text, borderColor: theme.colors.text },
  segText: { fontSize: 12, fontWeight: '600', color: theme.colors.text },
  segTextActive: { color: '#fff' },
  btn: { height: 52, backgroundColor: theme.colors.primary, borderRadius: 8, justifyContent: 'center', alignItems: 'center', marginTop: 32 },
  btnText: { color: '#fff', fontSize: 14, fontWeight: '700', letterSpacing: 1.5 },
});
