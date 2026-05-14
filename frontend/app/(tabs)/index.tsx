import { useEffect, useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api, formatBRL } from '../../src/api';
import { useAuth } from '../../src/auth';
import { theme } from '../../src/theme';

export default function Dashboard() {
  const { user, logout } = useAuth();
  const [stats, setStats] = useState<any>(null);
  const [indices, setIndices] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = async () => {
    try {
      const [s, i] = await Promise.all([api.get('/dashboard/stats'), api.get('/indices')]);
      setStats(s);
      setIndices(i);
    } catch (e) { console.log('Dashboard error', e); }
    finally { setLoading(false); setRefreshing(false); }
  };

  useFocusEffect(useCallback(() => { load(); }, []));

  if (loading) {
    return <View style={s.center}><ActivityIndicator size="large" color={theme.colors.primary} /></View>;
  }

  return (
    <SafeAreaView style={s.safe} edges={['top']}>
      <ScrollView refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}>
        <View style={s.header}>
          <View>
            <Text style={s.overline}>BEM-VINDO</Text>
            <Text style={s.h1}>{user?.full_name?.split(' ')[0] || 'Corretor'}</Text>
            {user?.company ? <Text style={s.company}>{user.company}</Text> : null}
          </View>
          <TouchableOpacity testID="logout-btn" onPress={logout} style={s.logoutBtn}>
            <Ionicons name="log-out-outline" size={22} color={theme.colors.text} />
          </TouchableOpacity>
        </View>

        <View style={s.heroCard}>
          <Text style={s.overlineLight}>RECEBIMENTOS DO MÊS</Text>
          <Text style={s.heroValue}>{formatBRL(stats?.receipts_month || 0)}</Text>
          <Text style={s.heroSubtitle}>Comissão: {formatBRL(stats?.commission_month || 0)}</Text>
        </View>

        <View style={s.kpiGrid}>
          <View style={s.kpiCard}>
            <Ionicons name="home-outline" size={20} color={theme.colors.primary} />
            <Text style={s.kpiValue}>{stats?.total_properties || 0}</Text>
            <Text style={s.kpiLabel}>IMÓVEIS ATIVOS</Text>
          </View>
          <View style={s.kpiCard}>
            <Ionicons name="people-outline" size={20} color={theme.colors.primary} />
            <Text style={s.kpiValue}>{stats?.total_clients || 0}</Text>
            <Text style={s.kpiLabel}>CLIENTES</Text>
          </View>
          <View style={s.kpiCard}>
            <Ionicons name="document-text-outline" size={20} color={theme.colors.primary} />
            <Text style={s.kpiValue}>{stats?.total_contracts || 0}</Text>
            <Text style={s.kpiLabel}>CONTRATOS</Text>
          </View>
          <View style={s.kpiCard}>
            <Ionicons name="cash-outline" size={20} color={theme.colors.success} />
            <Text style={[s.kpiValue, { fontSize: 18 }]}>{formatBRL(stats?.rent_portfolio || 0)}</Text>
            <Text style={s.kpiLabel}>CARTEIRA LOCAÇÃO/MÊS</Text>
          </View>
        </View>

        <View style={s.section}>
          <Text style={s.sectionTitle}>ÍNDICES DE MERCADO</Text>
          <View style={s.indicesRow}>
            <View style={s.indexCard}>
              <Text style={s.indexLabel}>IGPM 12M</Text>
              <Text style={s.indexValue}>{indices?.indices?.IGPM?.toFixed(2)}%</Text>
            </View>
            <View style={s.indexCard}>
              <Text style={s.indexLabel}>IPCA 12M</Text>
              <Text style={s.indexValue}>{indices?.indices?.IPCA?.toFixed(2)}%</Text>
            </View>
          </View>
          <Text style={s.indexNote}>{indices?.reference}</Text>
        </View>

        <View style={s.section}>
          <Text style={s.sectionTitle}>PORTFÓLIO DE VENDA</Text>
          <View style={s.portfolioCard}>
            <Text style={s.portfolioLabel}>Valor total</Text>
            <Text style={s.portfolioValue}>{formatBRL(stats?.sale_portfolio || 0)}</Text>
          </View>
        </View>
        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: theme.colors.bgSecondary },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: theme.colors.bg },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', padding: 24, backgroundColor: theme.colors.bg, borderBottomWidth: 1, borderBottomColor: theme.colors.border },
  overline: { fontSize: 10, color: theme.colors.textSecondary, letterSpacing: 2, fontWeight: '600' },
  overlineLight: { fontSize: 10, color: 'rgba(255,255,255,0.7)', letterSpacing: 2, fontWeight: '600' },
  h1: { fontSize: 28, fontWeight: '800', color: theme.colors.text, marginTop: 4, letterSpacing: -1 },
  company: { fontSize: 13, color: theme.colors.textSecondary, marginTop: 2 },
  logoutBtn: { padding: 10, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 8 },
  heroCard: { margin: 16, padding: 24, backgroundColor: theme.colors.text, borderRadius: 12 },
  heroValue: { fontSize: 36, fontWeight: '800', color: '#fff', marginTop: 8, letterSpacing: -1 },
  heroSubtitle: { fontSize: 13, color: 'rgba(255,255,255,0.8)', marginTop: 4 },
  kpiGrid: { flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 12 },
  kpiCard: { width: '48%', margin: '1%', padding: 16, backgroundColor: theme.colors.bg, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 8 },
  kpiValue: { fontSize: 24, fontWeight: '800', color: theme.colors.text, marginTop: 8, letterSpacing: -0.5 },
  kpiLabel: { fontSize: 9, color: theme.colors.textSecondary, letterSpacing: 1.5, marginTop: 4, fontWeight: '600' },
  section: { padding: 16, paddingTop: 24 },
  sectionTitle: { fontSize: 11, color: theme.colors.textSecondary, letterSpacing: 2, fontWeight: '700', marginBottom: 12 },
  indicesRow: { flexDirection: 'row', gap: 8 },
  indexCard: { flex: 1, padding: 16, backgroundColor: theme.colors.bg, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 8 },
  indexLabel: { fontSize: 10, color: theme.colors.textSecondary, letterSpacing: 1.5, fontWeight: '600' },
  indexValue: { fontSize: 24, fontWeight: '800', color: theme.colors.primary, marginTop: 6 },
  indexNote: { fontSize: 11, color: theme.colors.textDisabled, marginTop: 8, fontStyle: 'italic' },
  portfolioCard: { padding: 16, backgroundColor: theme.colors.bg, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 8 },
  portfolioLabel: { fontSize: 11, color: theme.colors.textSecondary, letterSpacing: 1.5, fontWeight: '600' },
  portfolioValue: { fontSize: 22, fontWeight: '800', color: theme.colors.text, marginTop: 6 },
});
