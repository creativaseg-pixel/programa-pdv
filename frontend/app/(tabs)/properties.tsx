import { useState, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, ActivityIndicator, Image, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api, formatBRL } from '../../src/api';
import { theme } from '../../src/theme';

const FALLBACK_IMG = 'https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=400';

export default function Properties() {
  const router = useRouter();
  const [items, setItems] = useState<any[]>([]);
  const [filter, setFilter] = useState<'all' | 'venda' | 'locacao'>('all');
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try { setItems(await api.get('/properties')); }
    catch (e: any) { Alert.alert('Erro', e.message); }
    finally { setLoading(false); }
  };

  useFocusEffect(useCallback(() => { load(); }, []));

  const filtered = items.filter(i => filter === 'all' || i.operation === filter);

  const del = (id: string) => {
    Alert.alert('Confirmar', 'Excluir este imóvel?', [
      { text: 'Cancelar' },
      { text: 'Excluir', style: 'destructive', onPress: async () => { await api.del(`/properties/${id}`); load(); } },
    ]);
  };

  return (
    <SafeAreaView style={s.safe} edges={['top']}>
      <View style={s.header}>
        <Text style={s.h1}>Imóveis</Text>
        <TouchableOpacity testID="add-property-btn" style={s.addBtn} onPress={() => router.push('/property-form')}>
          <Ionicons name="add" size={20} color="#fff" />
          <Text style={s.addBtnText}>NOVO</Text>
        </TouchableOpacity>
      </View>

      <View style={s.filters}>
        {(['all', 'venda', 'locacao'] as const).map(f => (
          <TouchableOpacity key={f} onPress={() => setFilter(f)} style={[s.chip, filter === f && s.chipActive]}>
            <Text style={[s.chipText, filter === f && s.chipTextActive]}>{f === 'all' ? 'Todos' : f === 'venda' ? 'Venda' : 'Locação'}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading ? <ActivityIndicator color={theme.colors.primary} style={{ marginTop: 40 }} /> :
        <FlatList
          data={filtered}
          keyExtractor={i => i.id}
          ListEmptyComponent={<Text style={s.empty}>Nenhum imóvel cadastrado. Toque em "NOVO" para começar.</Text>}
          contentContainerStyle={{ padding: 16 }}
          renderItem={({ item }) => (
            <TouchableOpacity testID={`property-${item.id}`} style={s.card} onPress={() => router.push({ pathname: '/property-form', params: { id: item.id } })} onLongPress={() => del(item.id)}>
              <Image source={{ uri: item.image_url || FALLBACK_IMG }} style={s.img} />
              <View style={s.cardInfo}>
                <View style={s.badge}>
                  <Text style={s.badgeText}>{item.operation === 'venda' ? 'VENDA' : 'LOCAÇÃO'}</Text>
                </View>
                <Text style={s.cardTitle} numberOfLines={1}>{item.title}</Text>
                <Text style={s.cardAddr} numberOfLines={1}>{item.address}, {item.city}/{item.state}</Text>
                <View style={s.cardMeta}>
                  <Text style={s.metaText}>{item.bedrooms}q · {item.bathrooms}b · {item.area}m²</Text>
                </View>
                <Text style={s.price}>{formatBRL(item.price)}{item.operation === 'locacao' ? '/mês' : ''}</Text>
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
  filters: { flexDirection: 'row', padding: 16, gap: 8, backgroundColor: theme.colors.bg, borderBottomWidth: 1, borderBottomColor: theme.colors.border },
  chip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, borderWidth: 1, borderColor: theme.colors.border },
  chipActive: { backgroundColor: theme.colors.text, borderColor: theme.colors.text },
  chipText: { fontSize: 12, color: theme.colors.text, fontWeight: '600' },
  chipTextActive: { color: '#fff' },
  empty: { textAlign: 'center', color: theme.colors.textSecondary, marginTop: 60, paddingHorizontal: 40 },
  card: { backgroundColor: theme.colors.bg, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 8, marginBottom: 12, overflow: 'hidden' },
  img: { width: '100%', height: 160, backgroundColor: theme.colors.bgSecondary },
  cardInfo: { padding: 16 },
  badge: { alignSelf: 'flex-start', backgroundColor: theme.colors.text, paddingHorizontal: 8, paddingVertical: 3, borderRadius: 3, marginBottom: 8 },
  badgeText: { color: '#fff', fontSize: 9, fontWeight: '700', letterSpacing: 1 },
  cardTitle: { fontSize: 17, fontWeight: '700', color: theme.colors.text },
  cardAddr: { fontSize: 13, color: theme.colors.textSecondary, marginTop: 2 },
  cardMeta: { marginTop: 8 },
  metaText: { fontSize: 12, color: theme.colors.textSecondary },
  price: { fontSize: 20, fontWeight: '800', color: theme.colors.primary, marginTop: 8, letterSpacing: -0.5 },
});
