import { useState, useEffect } from 'react';
import { View, Text, ScrollView, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform, Alert, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../src/api';
import { theme } from '../src/theme';

const TYPES = ['casa', 'apartamento', 'terreno', 'comercial'];

export default function PropertyForm() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id?: string }>();
  const [clients, setClients] = useState<any[]>([]);
  const [form, setForm] = useState<any>({
    title: '', type: 'apartamento', operation: 'venda', price: '',
    address: '', city: '', state: '', bedrooms: '0', bathrooms: '0', area: '0', garage: '0',
    description: '', image_url: '', owner_id: '', status: 'ativo',
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    (async () => {
      const cs = await api.get('/clients');
      setClients(cs.filter((c: any) => c.type === 'proprietario'));
      if (id) {
        const p = await api.get(`/properties/${id}`);
        setForm({ ...p, price: String(p.price), bedrooms: String(p.bedrooms), bathrooms: String(p.bathrooms), area: String(p.area), garage: String(p.garage) });
      }
    })();
  }, [id]);

  const update = (k: string, v: any) => setForm({ ...form, [k]: v });

  const save = async () => {
    if (!form.title || !form.price || !form.address) { Alert.alert('Erro', 'Título, preço e endereço são obrigatórios'); return; }
    setLoading(true);
    try {
      const payload = {
        ...form,
        price: parseFloat(form.price),
        bedrooms: parseInt(form.bedrooms) || 0,
        bathrooms: parseInt(form.bathrooms) || 0,
        area: parseFloat(form.area) || 0,
        garage: parseInt(form.garage) || 0,
      };
      if (id) await api.put(`/properties/${id}`, payload);
      else await api.post('/properties', payload);
      router.back();
    } catch (e: any) { Alert.alert('Erro', e.message); }
    finally { setLoading(false); }
  };

  return (
    <SafeAreaView style={s.safe}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Ionicons name="close" size={26} color={theme.colors.text} /></TouchableOpacity>
        <Text style={s.title}>{id ? 'Editar' : 'Novo'} Imóvel</Text>
        <View style={{ width: 26 }} />
      </View>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={{ padding: 20 }}>
          <Field label="Título *" value={form.title} onChange={(v: string) => update('title', v)} placeholder="Ex: Apto Vila Madalena" />

          <Text style={s.label}>Tipo</Text>
          <View style={s.segRow}>
            {TYPES.map(t => (
              <TouchableOpacity key={t} style={[s.seg, form.type === t && s.segActive]} onPress={() => update('type', t)}>
                <Text style={[s.segText, form.type === t && s.segTextActive]}>{t}</Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={s.label}>Operação</Text>
          <View style={s.segRow}>
            {['venda', 'locacao'].map(o => (
              <TouchableOpacity key={o} style={[s.seg, form.operation === o && s.segActive]} onPress={() => update('operation', o)}>
                <Text style={[s.segText, form.operation === o && s.segTextActive]}>{o === 'venda' ? 'Venda' : 'Locação'}</Text>
              </TouchableOpacity>
            ))}
          </View>

          <Field label="Valor (R$) *" value={form.price} onChange={(v: string) => update('price', v)} placeholder="0,00" keyboardType="decimal-pad" />
          <Field label="Endereço *" value={form.address} onChange={(v: string) => update('address', v)} placeholder="Rua, número" />
          <View style={{ flexDirection: 'row', gap: 12 }}>
            <View style={{ flex: 2 }}><Field label="Cidade" value={form.city} onChange={(v: string) => update('city', v)} /></View>
            <View style={{ flex: 1 }}><Field label="UF" value={form.state} onChange={(v: string) => update('state', v.toUpperCase().slice(0, 2))} /></View>
          </View>
          <View style={{ flexDirection: 'row', gap: 8 }}>
            <View style={{ flex: 1 }}><Field label="Quartos" value={form.bedrooms} onChange={(v: string) => update('bedrooms', v)} keyboardType="number-pad" /></View>
            <View style={{ flex: 1 }}><Field label="Banheiros" value={form.bathrooms} onChange={(v: string) => update('bathrooms', v)} keyboardType="number-pad" /></View>
            <View style={{ flex: 1 }}><Field label="Vagas" value={form.garage} onChange={(v: string) => update('garage', v)} keyboardType="number-pad" /></View>
            <View style={{ flex: 1 }}><Field label="Área m²" value={form.area} onChange={(v: string) => update('area', v)} keyboardType="decimal-pad" /></View>
          </View>
          <Field label="Imagem (URL)" value={form.image_url} onChange={(v: string) => update('image_url', v)} placeholder="https://..." />

          <Text style={s.label}>Proprietário</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <TouchableOpacity style={[s.chip, !form.owner_id && s.chipActive]} onPress={() => update('owner_id', '')}>
              <Text style={[s.chipText, !form.owner_id && s.chipTextActive]}>Nenhum</Text>
            </TouchableOpacity>
            {clients.map(c => (
              <TouchableOpacity key={c.id} style={[s.chip, form.owner_id === c.id && s.chipActive]} onPress={() => update('owner_id', c.id)}>
                <Text style={[s.chipText, form.owner_id === c.id && s.chipTextActive]}>{c.name}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          <Field label="Descrição" value={form.description} onChange={(v: string) => update('description', v)} multiline />

          <TouchableOpacity testID="property-save-btn" style={s.btn} onPress={save} disabled={loading}>
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
  segRow: { flexDirection: 'row', gap: 6, flexWrap: 'wrap' },
  seg: { paddingVertical: 10, paddingHorizontal: 14, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 6, backgroundColor: theme.colors.bg },
  segActive: { backgroundColor: theme.colors.text, borderColor: theme.colors.text },
  segText: { fontSize: 12, fontWeight: '600', color: theme.colors.text, textTransform: 'capitalize' },
  segTextActive: { color: '#fff' },
  chip: { paddingHorizontal: 14, paddingVertical: 8, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 20, marginRight: 6 },
  chipActive: { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary },
  chipText: { fontSize: 12, color: theme.colors.text, fontWeight: '600' },
  chipTextActive: { color: '#fff' },
  btn: { height: 52, backgroundColor: theme.colors.primary, borderRadius: 8, justifyContent: 'center', alignItems: 'center', marginTop: 32 },
  btnText: { color: '#fff', fontSize: 14, fontWeight: '700', letterSpacing: 1.5 },
});
