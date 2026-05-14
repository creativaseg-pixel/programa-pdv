import { useState, useEffect } from 'react';
import { View, Text, ScrollView, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform, Alert, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../src/api';
import { theme } from '../src/theme';

const TYPES = [
  { k: 'aluguel', l: 'Aluguel' },
  { k: 'sinal', l: 'Sinal' },
  { k: 'comissao', l: 'Comissão' },
];
const METHODS = ['PIX', 'Dinheiro', 'Transferência', 'Boleto', 'Cartão'];

export default function ReceiptForm() {
  const router = useRouter();
  const [clients, setClients] = useState<any[]>([]);
  const [form, setForm] = useState<any>({
    type: 'aluguel', payer_id: '', receiver_id: '', value: '',
    reference: '', payment_date: new Date().toISOString().slice(0, 10),
    payment_method: 'PIX', notes: '',
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => { api.get('/clients').then(setClients); }, []);

  const update = (k: string, v: any) => setForm({ ...form, [k]: v });

  const save = async () => {
    if (!form.payer_id || !form.receiver_id || !form.value || !form.reference) {
      Alert.alert('Erro', 'Pagador, recebedor, valor e referência são obrigatórios');
      return;
    }
    setLoading(true);
    try {
      await api.post('/receipts', { ...form, value: parseFloat(form.value) });
      router.back();
    } catch (e: any) { Alert.alert('Erro', e.message); }
    finally { setLoading(false); }
  };

  return (
    <SafeAreaView style={s.safe}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Ionicons name="close" size={26} color={theme.colors.text} /></TouchableOpacity>
        <Text style={s.title}>Novo Recibo</Text>
        <View style={{ width: 26 }} />
      </View>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={{ padding: 20 }}>
          <Text style={s.label}>Tipo</Text>
          <View style={s.segRow}>
            {TYPES.map(t => (
              <TouchableOpacity key={t.k} style={[s.seg, form.type === t.k && s.segActive]} onPress={() => update('type', t.k)}>
                <Text style={[s.segText, form.type === t.k && s.segTextActive]}>{t.l}</Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={s.label}>Pagador *</Text>
          <ClientPicker list={clients} value={form.payer_id} onPick={(v: string) => update('payer_id', v)} />

          <Text style={s.label}>Recebedor *</Text>
          <ClientPicker list={clients} value={form.receiver_id} onPick={(v: string) => update('receiver_id', v)} />

          <Field label="Valor (R$) *" value={form.value} onChange={(v: string) => update('value', v)} keyboardType="decimal-pad" />
          <Field label="Referência *" value={form.reference} onChange={(v: string) => update('reference', v)} placeholder="Ex: Aluguel ref. Jan/2026" />
          <Field label="Data do pagamento" value={form.payment_date} onChange={(v: string) => update('payment_date', v)} placeholder="YYYY-MM-DD" />

          <Text style={s.label}>Forma de pagamento</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {METHODS.map(m => (
              <TouchableOpacity key={m} style={[s.chip, form.payment_method === m && s.chipActive]} onPress={() => update('payment_method', m)}>
                <Text style={[s.chipText, form.payment_method === m && s.chipTextActive]}>{m}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          <Field label="Observações" value={form.notes} onChange={(v: string) => update('notes', v)} multiline />

          <TouchableOpacity testID="receipt-save-btn" style={s.btn} onPress={save} disabled={loading}>
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={s.btnText}>EMITIR RECIBO</Text>}
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function ClientPicker({ list, value, onPick }: any) {
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false}>
      {list.length === 0 ? <Text style={s.hint}>Cadastre clientes primeiro</Text> : list.map((c: any) => (
        <TouchableOpacity key={c.id} style={[s.chip, value === c.id && s.chipActive]} onPress={() => onPick(c.id)}>
          <Text style={[s.chipText, value === c.id && s.chipTextActive]}>{c.name}</Text>
        </TouchableOpacity>
      ))}
    </ScrollView>
  );
}

function Field({ label, value, onChange, placeholder, keyboardType, multiline }: any) {
  return (
    <View>
      <Text style={s.label}>{label}</Text>
      <TextInput style={[s.input, multiline && { height: 70, textAlignVertical: 'top' }]} value={value} onChangeText={onChange} placeholder={placeholder} placeholderTextColor={theme.colors.textDisabled} keyboardType={keyboardType} multiline={multiline} />
    </View>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: theme.colors.bg },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 20, borderBottomWidth: 1, borderBottomColor: theme.colors.border },
  title: { fontSize: 18, fontWeight: '700', color: theme.colors.text },
  label: { fontSize: 11, color: theme.colors.textSecondary, letterSpacing: 1.5, marginBottom: 8, marginTop: 16, fontWeight: '600' },
  hint: { fontSize: 12, color: theme.colors.danger, fontStyle: 'italic' },
  input: { height: 48, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 8, paddingHorizontal: 14, fontSize: 15, color: theme.colors.text },
  segRow: { flexDirection: 'row', gap: 6 },
  seg: { flex: 1, paddingVertical: 12, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 6, backgroundColor: theme.colors.bg, alignItems: 'center' },
  segActive: { backgroundColor: theme.colors.text, borderColor: theme.colors.text },
  segText: { fontSize: 12, fontWeight: '600', color: theme.colors.text },
  segTextActive: { color: '#fff' },
  chip: { paddingHorizontal: 14, paddingVertical: 10, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 20, marginRight: 6 },
  chipActive: { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary },
  chipText: { fontSize: 13, color: theme.colors.text, fontWeight: '600' },
  chipTextActive: { color: '#fff' },
  btn: { height: 52, backgroundColor: theme.colors.primary, borderRadius: 8, justifyContent: 'center', alignItems: 'center', marginTop: 32 },
  btnText: { color: '#fff', fontSize: 14, fontWeight: '700', letterSpacing: 1.5 },
});
