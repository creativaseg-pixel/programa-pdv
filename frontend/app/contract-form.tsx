import { useState, useEffect } from 'react';
import { View, Text, ScrollView, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform, Alert, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api, formatBRL } from '../src/api';
import { theme } from '../src/theme';

export default function ContractForm() {
  const router = useRouter();
  const [properties, setProperties] = useState<any[]>([]);
  const [clients, setClients] = useState<any[]>([]);
  const [form, setForm] = useState<any>({
    type: 'locacao', property_id: '', landlord_id: '', tenant_id: '',
    value: '', start_date: new Date().toISOString().slice(0, 10), end_date: '',
    payment_day: '5', index: 'IGPM', commission_pct: '100', deposit_value: '', extra_terms: '',
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    (async () => {
      const [p, c] = await Promise.all([api.get('/properties'), api.get('/clients')]);
      setProperties(p);
      setClients(c);
    })();
  }, []);

  const update = (k: string, v: any) => setForm({ ...form, [k]: v });

  const landlords = clients.filter(c => c.type === 'proprietario');
  const tenants = clients.filter(c => c.type === (form.type === 'locacao' ? 'inquilino' : 'comprador'));

  const save = async () => {
    if (!form.property_id || !form.landlord_id || !form.tenant_id || !form.value) {
      Alert.alert('Erro', 'Preencha imóvel, partes envolvidas e valor');
      return;
    }
    setLoading(true);
    try {
      await api.post('/contracts', {
        ...form,
        value: parseFloat(form.value),
        payment_day: parseInt(form.payment_day) || 5,
        commission_pct: parseFloat(form.commission_pct) || 0,
        deposit_value: parseFloat(form.deposit_value) || 0,
      });
      router.back();
    } catch (e: any) { Alert.alert('Erro', e.message); }
    finally { setLoading(false); }
  };

  return (
    <SafeAreaView style={s.safe}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Ionicons name="close" size={26} color={theme.colors.text} /></TouchableOpacity>
        <Text style={s.title}>Novo Contrato</Text>
        <View style={{ width: 26 }} />
      </View>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={{ padding: 20 }}>
          <Text style={s.label}>Tipo de contrato</Text>
          <View style={s.segRow}>
            {[{ k: 'locacao', l: 'Locação' }, { k: 'compra_venda', l: 'Compra e Venda' }].map(t => (
              <TouchableOpacity key={t.k} style={[s.seg, form.type === t.k && s.segActive]} onPress={() => update('type', t.k)}>
                <Text style={[s.segText, form.type === t.k && s.segTextActive]}>{t.l}</Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={s.label}>Imóvel *</Text>
          {properties.length === 0 ? <Text style={s.hint}>Cadastre um imóvel primeiro</Text> :
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              {properties.map(p => (
                <TouchableOpacity key={p.id} style={[s.chipLarge, form.property_id === p.id && s.chipActive]} onPress={() => { update('property_id', p.id); if (!form.value) update('value', String(p.price)); }}>
                  <Text style={[s.chipTitle, form.property_id === p.id && { color: '#fff' }]} numberOfLines={1}>{p.title}</Text>
                  <Text style={[s.chipSub, form.property_id === p.id && { color: 'rgba(255,255,255,0.8)' }]}>{formatBRL(p.price)}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          }

          <Text style={s.label}>{form.type === 'locacao' ? 'Locador (Proprietário) *' : 'Vendedor *'}</Text>
          {landlords.length === 0 ? <Text style={s.hint}>Cadastre um proprietário</Text> : <ClientPicker list={landlords} value={form.landlord_id} onPick={(v: string) => update('landlord_id', v)} />}

          <Text style={s.label}>{form.type === 'locacao' ? 'Locatário (Inquilino) *' : 'Comprador *'}</Text>
          {tenants.length === 0 ? <Text style={s.hint}>Cadastre um {form.type === 'locacao' ? 'inquilino' : 'comprador'}</Text> : <ClientPicker list={tenants} value={form.tenant_id} onPick={(v: string) => update('tenant_id', v)} />}

          <Field label="Valor (R$) *" value={form.value} onChange={(v: string) => update('value', v)} keyboardType="decimal-pad" />
          <View style={{ flexDirection: 'row', gap: 12 }}>
            <View style={{ flex: 1 }}><Field label="Início (YYYY-MM-DD)" value={form.start_date} onChange={(v: string) => update('start_date', v)} /></View>
            <View style={{ flex: 1 }}><Field label="Fim (YYYY-MM-DD)" value={form.end_date} onChange={(v: string) => update('end_date', v)} placeholder="opcional" /></View>
          </View>

          {form.type === 'locacao' && (
            <>
              <View style={{ flexDirection: 'row', gap: 12 }}>
                <View style={{ flex: 1 }}><Field label="Dia pagamento" value={form.payment_day} onChange={(v: string) => update('payment_day', v)} keyboardType="number-pad" /></View>
                <View style={{ flex: 1 }}><Field label="Caução (R$)" value={form.deposit_value} onChange={(v: string) => update('deposit_value', v)} keyboardType="decimal-pad" /></View>
              </View>
              <Text style={s.label}>Índice de reajuste anual</Text>
              <View style={s.segRow}>
                {['IGPM', 'IPCA'].map(i => (
                  <TouchableOpacity key={i} style={[s.seg, form.index === i && s.segActive]} onPress={() => update('index', i)}>
                    <Text style={[s.segText, form.index === i && s.segTextActive]}>{i}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </>
          )}

          <Field label="Comissão (%)" value={form.commission_pct} onChange={(v: string) => update('commission_pct', v)} keyboardType="decimal-pad" />
          <Field label="Cláusulas adicionais" value={form.extra_terms} onChange={(v: string) => update('extra_terms', v)} multiline />

          <TouchableOpacity testID="contract-save-btn" style={s.btn} onPress={save} disabled={loading}>
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={s.btnText}>SALVAR CONTRATO</Text>}
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function ClientPicker({ list, value, onPick }: any) {
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false}>
      {list.map((c: any) => (
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
  chipLarge: { width: 180, padding: 12, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 8, marginRight: 8 },
  chipActive: { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary },
  chipText: { fontSize: 13, color: theme.colors.text, fontWeight: '600' },
  chipTextActive: { color: '#fff' },
  chipTitle: { fontSize: 13, color: theme.colors.text, fontWeight: '700' },
  chipSub: { fontSize: 11, color: theme.colors.textSecondary, marginTop: 4 },
  btn: { height: 52, backgroundColor: theme.colors.primary, borderRadius: 8, justifyContent: 'center', alignItems: 'center', marginTop: 32 },
  btnText: { color: '#fff', fontSize: 14, fontWeight: '700', letterSpacing: 1.5 },
});
