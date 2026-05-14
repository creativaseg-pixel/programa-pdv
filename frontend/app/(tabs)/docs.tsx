import { useState, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, ActivityIndicator, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api, formatBRL, formatDate } from '../../src/api';
import { theme } from '../../src/theme';

export default function Docs() {
  const router = useRouter();
  const [tab, setTab] = useState<'contracts' | 'receipts'>('contracts');
  const [contracts, setContracts] = useState<any[]>([]);
  const [receipts, setReceipts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [c, r] = await Promise.all([api.get('/contracts'), api.get('/receipts')]);
      setContracts(c); setReceipts(r);
    } catch (e: any) { Alert.alert('Erro', e.message); }
    finally { setLoading(false); }
  };

  useFocusEffect(useCallback(() => { load(); }, []));

  const del = (kind: 'contracts' | 'receipts', id: string) => {
    Alert.alert('Confirmar', 'Excluir?', [
      { text: 'Cancelar' },
      { text: 'Excluir', style: 'destructive', onPress: async () => { await api.del(`/${kind}/${id}`); load(); } },
    ]);
  };

  return (
    <SafeAreaView style={s.safe} edges={['top']}>
      <View style={s.header}>
        <Text style={s.h1}>Documentos</Text>
        <TouchableOpacity testID="add-doc-btn" style={s.addBtn} onPress={() => router.push(tab === 'contracts' ? '/contract-form' : '/receipt-form')}>
          <Ionicons name="add" size={20} color="#fff" />
          <Text style={s.addBtnText}>NOVO</Text>
        </TouchableOpacity>
      </View>
      <View style={s.tabs}>
        <TouchableOpacity testID="tab-contracts" style={[s.tab, tab === 'contracts' && s.tabActive]} onPress={() => setTab('contracts')}>
          <Text style={[s.tabText, tab === 'contracts' && s.tabTextActive]}>Contratos ({contracts.length})</Text>
        </TouchableOpacity>
        <TouchableOpacity testID="tab-receipts" style={[s.tab, tab === 'receipts' && s.tabActive]} onPress={() => setTab('receipts')}>
          <Text style={[s.tabText, tab === 'receipts' && s.tabTextActive]}>Recibos ({receipts.length})</Text>
        </TouchableOpacity>
      </View>

      {loading ? <ActivityIndicator color={theme.colors.primary} style={{ marginTop: 40 }} /> : tab === 'contracts' ? (
        <FlatList
          data={contracts}
          keyExtractor={i => i.id}
          ListEmptyComponent={<Text style={s.empty}>Nenhum contrato. Toque "NOVO".</Text>}
          contentContainerStyle={{ padding: 16 }}
          renderItem={({ item }) => (
            <TouchableOpacity testID={`contract-${item.id}`} style={s.card} onPress={() => router.push({ pathname: '/contract-view', params: { id: item.id } })} onLongPress={() => del('contracts', item.id)}>
              <View style={s.cardLeft}>
                <Ionicons name="document-text" size={28} color={theme.colors.primary} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={s.cardOver}>{item.type === 'locacao' ? 'LOCAÇÃO' : 'COMPRA E VENDA'}</Text>
                <Text style={s.cardTitle}>{formatBRL(item.value)}{item.type === 'locacao' ? '/mês' : ''}</Text>
                <Text style={s.cardSub}>Início: {formatDate(item.start_date)} · {item.index}</Text>
              </View>
              <Ionicons name="chevron-forward" size={20} color={theme.colors.textDisabled} />
            </TouchableOpacity>
          )}
        />
      ) : (
        <FlatList
          data={receipts}
          keyExtractor={i => i.id}
          ListEmptyComponent={<Text style={s.empty}>Nenhum recibo emitido.</Text>}
          contentContainerStyle={{ padding: 16 }}
          renderItem={({ item }) => (
            <TouchableOpacity testID={`receipt-${item.id}`} style={s.card} onPress={() => router.push({ pathname: '/receipt-view', params: { id: item.id } })} onLongPress={() => del('receipts', item.id)}>
              <View style={s.cardLeft}>
                <Ionicons name="receipt" size={28} color={theme.colors.success} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={s.cardOver}>{item.receipt_number}</Text>
                <Text style={s.cardTitle}>{formatBRL(item.value)}</Text>
                <Text style={s.cardSub}>{item.reference} · {formatDate(item.payment_date)}</Text>
              </View>
              <Ionicons name="chevron-forward" size={20} color={theme.colors.textDisabled} />
            </TouchableOpacity>
          )}
        />
      )}
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: theme.colors.bgSecondary },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 24, paddingBottom: 12, backgroundColor: theme.colors.bg, borderBottomWidth: 1, borderBottomColor: theme.colors.border },
  h1: { fontSize: 28, fontWeight: '800', color: theme.colors.text, letterSpacing: -1 },
  addBtn: { flexDirection: 'row', alignItems: 'center', backgroundColor: theme.colors.primary, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 6, gap: 4 },
  addBtnText: { color: '#fff', fontWeight: '700', fontSize: 12, letterSpacing: 1 },
  tabs: { flexDirection: 'row', backgroundColor: theme.colors.bg, borderBottomWidth: 1, borderBottomColor: theme.colors.border },
  tab: { flex: 1, paddingVertical: 14, alignItems: 'center', borderBottomWidth: 2, borderBottomColor: 'transparent' },
  tabActive: { borderBottomColor: theme.colors.primary },
  tabText: { fontSize: 13, fontWeight: '600', color: theme.colors.textSecondary },
  tabTextActive: { color: theme.colors.primary },
  empty: { textAlign: 'center', color: theme.colors.textSecondary, marginTop: 60 },
  card: { flexDirection: 'row', alignItems: 'center', backgroundColor: theme.colors.bg, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 8, padding: 16, marginBottom: 10, gap: 12 },
  cardLeft: { width: 40, alignItems: 'center' },
  cardOver: { fontSize: 10, color: theme.colors.textSecondary, letterSpacing: 1.5, fontWeight: '700' },
  cardTitle: { fontSize: 18, fontWeight: '800', color: theme.colors.text, marginTop: 2 },
  cardSub: { fontSize: 12, color: theme.colors.textSecondary, marginTop: 2 },
});
