import { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TextInput, TouchableOpacity, ActivityIndicator, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { api, formatBRL } from '../../src/api';
import { theme } from '../../src/theme';

type Tab = 'reajuste' | 'multa' | 'comissao';

export default function Finance() {
  const [tab, setTab] = useState<Tab>('reajuste');
  return (
    <SafeAreaView style={s.safe} edges={['top']}>
      <View style={s.header}>
        <Text style={s.h1}>Calculadora</Text>
        <Text style={s.sub}>Cálculos automáticos do mercado imobiliário</Text>
      </View>
      <View style={s.tabs}>
        {(['reajuste', 'multa', 'comissao'] as Tab[]).map(t => (
          <TouchableOpacity key={t} testID={`tab-${t}`} style={[s.tab, tab === t && s.tabActive]} onPress={() => setTab(t)}>
            <Text style={[s.tabText, tab === t && s.tabTextActive]}>
              {t === 'reajuste' ? 'Reajuste' : t === 'multa' ? 'Multa/Juros' : 'Comissão'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={{ padding: 16 }}>
          {tab === 'reajuste' && <Reajuste />}
          {tab === 'multa' && <Multa />}
          {tab === 'comissao' && <Comissao />}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function Reajuste() {
  const [valor, setValor] = useState('');
  const [indice, setIndice] = useState<'IGPM' | 'IPCA'>('IGPM');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const calc = async () => {
    if (!valor) return;
    setLoading(true);
    try { setResult(await api.post('/calc/reajuste', { valor_atual: parseFloat(valor), indice })); }
    catch (e: any) { Alert.alert('Erro', e.message); }
    finally { setLoading(false); }
  };
  return (
    <View>
      <Text style={s.label}>Valor atual do aluguel</Text>
      <TextInput testID="reajuste-valor" style={s.input} value={valor} onChangeText={setValor} placeholder="0,00" keyboardType="decimal-pad" />
      <Text style={s.label}>Índice de reajuste</Text>
      <View style={s.segRow}>
        {(['IGPM', 'IPCA'] as const).map(i => (
          <TouchableOpacity key={i} testID={`indice-${i}`} style={[s.seg, indice === i && s.segActive]} onPress={() => setIndice(i)}>
            <Text style={[s.segText, indice === i && s.segTextActive]}>{i}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <TouchableOpacity testID="calc-reajuste" style={s.btn} onPress={calc} disabled={loading}>
        {loading ? <ActivityIndicator color="#fff" /> : <Text style={s.btnText}>CALCULAR</Text>}
      </TouchableOpacity>
      {result && <ResultCard title="Resultado do reajuste" rows={[
        ['Valor atual', formatBRL(result.valor_atual)],
        [`${result.indice} aplicado`, `${result.percentual_aplicado}%`],
        ['Diferença', formatBRL(result.diferenca)],
        ['Novo valor', formatBRL(result.novo_valor), true],
      ]} />}
    </View>
  );
}

function Multa() {
  const [valor, setValor] = useState('');
  const [dias, setDias] = useState('');
  const [multa, setMulta] = useState('10');
  const [juros, setJuros] = useState('1');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const calc = async () => {
    if (!valor || !dias) return;
    setLoading(true);
    try { setResult(await api.post('/calc/multa-juros', { valor_devido: parseFloat(valor), dias_atraso: parseInt(dias), multa_pct: parseFloat(multa), juros_mes_pct: parseFloat(juros) })); }
    catch (e: any) { Alert.alert('Erro', e.message); }
    finally { setLoading(false); }
  };
  return (
    <View>
      <Text style={s.label}>Valor devido</Text>
      <TextInput testID="multa-valor" style={s.input} value={valor} onChangeText={setValor} placeholder="0,00" keyboardType="decimal-pad" />
      <Text style={s.label}>Dias em atraso</Text>
      <TextInput testID="multa-dias" style={s.input} value={dias} onChangeText={setDias} placeholder="0" keyboardType="number-pad" />
      <View style={{ flexDirection: 'row', gap: 12 }}>
        <View style={{ flex: 1 }}>
          <Text style={s.label}>Multa %</Text>
          <TextInput style={s.input} value={multa} onChangeText={setMulta} keyboardType="decimal-pad" />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={s.label}>Juros % a.m.</Text>
          <TextInput style={s.input} value={juros} onChangeText={setJuros} keyboardType="decimal-pad" />
        </View>
      </View>
      <Text style={s.hint}>Padrão Lei do Inquilinato: multa 10% + 1% a.m.</Text>
      <TouchableOpacity testID="calc-multa" style={s.btn} onPress={calc} disabled={loading}>
        {loading ? <ActivityIndicator color="#fff" /> : <Text style={s.btnText}>CALCULAR</Text>}
      </TouchableOpacity>
      {result && <ResultCard title="Total com encargos" rows={[
        ['Valor original', formatBRL(result.valor_devido)],
        ['Multa', formatBRL(result.multa)],
        [`Juros (${result.dias_atraso} dias)`, formatBRL(result.juros)],
        ['Total a pagar', formatBRL(result.total), true],
      ]} />}
    </View>
  );
}

function Comissao() {
  const [valor, setValor] = useState('');
  const [tipo, setTipo] = useState<'venda' | 'locacao'>('venda');
  const [pct, setPct] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const calc = async () => {
    if (!valor) return;
    setLoading(true);
    try { 
      const body: any = { valor_transacao: parseFloat(valor), tipo };
      if (pct) body.percentual = parseFloat(pct);
      setResult(await api.post('/calc/comissao', body));
    }
    catch (e: any) { Alert.alert('Erro', e.message); }
    finally { setLoading(false); }
  };
  return (
    <View>
      <Text style={s.label}>Valor da transação</Text>
      <TextInput testID="com-valor" style={s.input} value={valor} onChangeText={setValor} placeholder="0,00" keyboardType="decimal-pad" />
      <Text style={s.label}>Tipo</Text>
      <View style={s.segRow}>
        {(['venda', 'locacao'] as const).map(t => (
          <TouchableOpacity key={t} testID={`tipo-${t}`} style={[s.seg, tipo === t && s.segActive]} onPress={() => setTipo(t)}>
            <Text style={[s.segText, tipo === t && s.segTextActive]}>{t === 'venda' ? 'Venda' : 'Locação'}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <Text style={s.label}>Percentual personalizado (opcional)</Text>
      <TextInput style={s.input} value={pct} onChangeText={setPct} placeholder={tipo === 'venda' ? '6.0 (padrão COFECI)' : '100 (1 aluguel)'} keyboardType="decimal-pad" />
      <Text style={s.hint}>Padrão de mercado: 6% para venda, 1 aluguel (100%) para locação</Text>
      <TouchableOpacity testID="calc-com" style={s.btn} onPress={calc} disabled={loading}>
        {loading ? <ActivityIndicator color="#fff" /> : <Text style={s.btnText}>CALCULAR</Text>}
      </TouchableOpacity>
      {result && <ResultCard title="Comissão calculada" rows={[
        ['Valor da transação', formatBRL(result.valor_transacao)],
        ['Tipo', result.tipo === 'venda' ? 'Venda' : 'Locação'],
        ['Percentual', `${result.percentual}%`],
        ['Comissão', formatBRL(result.comissao), true],
      ]} />}
    </View>
  );
}

function ResultCard({ title, rows }: { title: string; rows: any[] }) {
  return (
    <View style={s.resultCard} testID="calc-result">
      <View style={s.resultHeader}>
        <Ionicons name="checkmark-circle" size={20} color={theme.colors.success} />
        <Text style={s.resultTitle}>{title}</Text>
      </View>
      {rows.map(([label, value, highlight]: any, i: number) => (
        <View key={i} style={[s.row, i === rows.length - 1 && s.lastRow]}>
          <Text style={s.rowLabel}>{label}</Text>
          <Text style={[s.rowValue, highlight && s.rowHighlight]}>{value}</Text>
        </View>
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: theme.colors.bgSecondary },
  header: { padding: 24, paddingBottom: 16, backgroundColor: theme.colors.bg, borderBottomWidth: 1, borderBottomColor: theme.colors.border },
  h1: { fontSize: 28, fontWeight: '800', color: theme.colors.text, letterSpacing: -1 },
  sub: { fontSize: 13, color: theme.colors.textSecondary, marginTop: 4 },
  tabs: { flexDirection: 'row', backgroundColor: theme.colors.bg, borderBottomWidth: 1, borderBottomColor: theme.colors.border },
  tab: { flex: 1, paddingVertical: 14, alignItems: 'center', borderBottomWidth: 2, borderBottomColor: 'transparent' },
  tabActive: { borderBottomColor: theme.colors.primary },
  tabText: { fontSize: 13, fontWeight: '600', color: theme.colors.textSecondary },
  tabTextActive: { color: theme.colors.primary },
  label: { fontSize: 11, color: theme.colors.textSecondary, letterSpacing: 1.5, marginBottom: 8, marginTop: 16, fontWeight: '600' },
  input: { height: 52, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 8, paddingHorizontal: 16, fontSize: 16, color: theme.colors.text, backgroundColor: theme.colors.bg },
  segRow: { flexDirection: 'row', gap: 8 },
  seg: { flex: 1, paddingVertical: 14, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 8, alignItems: 'center', backgroundColor: theme.colors.bg },
  segActive: { backgroundColor: theme.colors.text, borderColor: theme.colors.text },
  segText: { fontSize: 13, fontWeight: '700', color: theme.colors.text },
  segTextActive: { color: '#fff' },
  hint: { fontSize: 11, color: theme.colors.textDisabled, marginTop: 8, fontStyle: 'italic' },
  btn: { height: 52, backgroundColor: theme.colors.primary, borderRadius: 8, justifyContent: 'center', alignItems: 'center', marginTop: 24 },
  btnText: { color: '#fff', fontSize: 14, fontWeight: '700', letterSpacing: 1.5 },
  resultCard: { marginTop: 24, padding: 20, backgroundColor: theme.colors.bg, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 8 },
  resultHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 16 },
  resultTitle: { fontSize: 14, fontWeight: '700', color: theme.colors.text, letterSpacing: 0.5 },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: theme.colors.border },
  lastRow: { borderBottomWidth: 0, marginTop: 4, paddingTop: 14 },
  rowLabel: { fontSize: 13, color: theme.colors.textSecondary },
  rowValue: { fontSize: 14, fontWeight: '600', color: theme.colors.text },
  rowHighlight: { fontSize: 20, fontWeight: '800', color: theme.colors.primary, letterSpacing: -0.5 },
});
