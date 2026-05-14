import { useState, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, ActivityIndicator, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../../src/api';
import { theme } from '../../src/theme';

const TYPE_LABELS: any = { proprietario: 'Proprietário', inquilino: 'Inquilino', comprador: 'Comprador' };
const TYPE_COLORS: any = { proprietario: theme.colors.luxury, inquilino: theme.colors.primary, comprador: theme.colors.success };

export default function Clients() {
  const router = useRouter();
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  const load = async () => {
    setLoading(true);
    try { setItems(await api.get('/clients')); }
    catch (e: any) { Alert.alert('Erro', e.message); }
    finally { setLoading(false); }
  };

  useFocusEffect(useCallback(() => { load(); }, []));

  const filtered = filter === 'all' ? items : items.filter(i => i.type === filter);

  const del = (id: string) => {
    Alert.alert('Confirmar', 'Excluir cliente?', [
      { text: 'Cancelar' },
      { text: 'Excluir', style: 'destructive', onPress: async () => { await api.del(`/clients/${id}`); load(); } },
    ]);
  };

  return (
    <SafeAreaView style={s.safe} edges={['top']}>
      <View style={s.header}>
        <Text style={s.h1}>Clientes</Text>
        <TouchableOpacity testID="add-client-btn" style={s.addBtn} onPress={() => router.push('/client-form')}>
          <Ionicons name="add" size={20} color="#fff" />
          <Text style={s.addBtnText}>NOVO</Text>
        </TouchableOpacity>
      </View>

      <View style={s.filters}>
        {['all', 'proprietario', 'inquilino', 'comprador'].map(f => (
          <TouchableOpacity key={f} onPress={() => setFilter(f)} style={[s.chip, filter === f && s.chipActive]}>
            <Text style={[s.chipText, filter === f && s.chipTextActive]}>{f === 'all' ? 'Todos' : TYPE_LABELS[f]}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading ? <ActivityIndicator color={theme.colors.primary} style={{ marginTop: 40 }} /> :
        <FlatList
          data={filtered}
          keyExtractor={i => i.id}
          ListEmptyComponent={<Text style={s.empty}>Nenhum cliente cadastrado.</Text>}
          contentContainerStyle={{ padding: 16 }}
          renderItem={({ item }) => (
            <TouchableOpacity testID={`client-${item.id}`} style={s.card} onPress={() => router.push({ pathname: '/client-form', params: { id: item.id } })} onLongPress={() => del(item.id)}>
              <View style={[s.avatar, { backgroundColor: TYPE_COLORS[item.type] || theme.colors.primary }]}>
                <Text style={s.avatarText}>{item.name?.[0]?.toUpperCase()}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={s.cardTitle}>{item.name}</Text>
                <Text style={s.cardSub}>{item.cpf_cnpj} · {item.phone}</Text>
                <Text style={[s.type, { color: TYPE_COLORS[item.type] }]}>{TYPE_LABELS[item.type] || item.type}</Text>
              </View>
            </TouchableOpacity>
          )}
        />
      }
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: theme.colors.bgSecondary },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 24, paddingBottom: 12, backgroundColor: theme.colors.bg, borderBottomWidth: 1, borderBottomColor: theme.colors.border },
  h1: { fontSize: 28, fontWeight: '800', color: theme.colors.text, letterSpacing: -1 },
  addBtn: { flexDirection: 'row', alignItems: 'center', backgroundColor: theme.colors.primary, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 6, gap: 4 },
  addBtnText: { color: '#fff', fontWeight: '700', fontSize: 12, letterSpacing: 1 },
  filters: { flexDirection: 'row', padding: 16, gap: 8, backgroundColor: theme.colors.bg, borderBottomWidth: 1, borderBottomColor: theme.colors.border, flexWrap: 'wrap' },
  chip: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20, borderWidth: 1, borderColor: theme.colors.border },
  chipActive: { backgroundColor: theme.colors.text, borderColor: theme.colors.text },
  chipText: { fontSize: 11, color: theme.colors.text, fontWeight: '600' },
  chipTextActive: { color: '#fff' },
  empty: { textAlign: 'center', color: theme.colors.textSecondary, marginTop: 60 },
  card: { flexDirection: 'row', backgroundColor: theme.colors.bg, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 8, padding: 16, marginBottom: 10, alignItems: 'center', gap: 16 },
  avatar: { width: 48, height: 48, borderRadius: 24, justifyContent: 'center', alignItems: 'center' },
  avatarText: { color: '#fff', fontSize: 20, fontWeight: '800' },
  cardTitle: { fontSize: 16, fontWeight: '700', color: theme.colors.text },
  cardSub: { fontSize: 12, color: theme.colors.textSecondary, marginTop: 2 },
  type: { fontSize: 11, fontWeight: '700', marginTop: 4, letterSpacing: 1, textTransform: 'uppercase' },
});
