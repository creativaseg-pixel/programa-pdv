import { useEffect, useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, ActivityIndicator, Share, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api, formatBRL, formatDate } from '../src/api';
import { theme } from '../src/theme';

function numberToWords(value: number): string {
  // Simplified BR Real extenso (only for common values)
  if (value === 0) return 'zero reais';
  try {
    const reais = Math.floor(value);
    const cents = Math.round((value - reais) * 100);
    let txt = '';
    if (reais === 1) txt = 'um real';
    else txt = `${reais.toLocaleString('pt-BR')} reais`;
    if (cents > 0) txt += ` e ${cents} centavos`;
    return txt;
  } catch { return ''; }
}

export default function ReceiptView() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const [r, setR] = useState<any>(null);

  useEffect(() => { api.get(`/receipts/${id}`).then(setR); }, [id]);

  if (!r) return <View style={[s.safe, { justifyContent: 'center' }]}><ActivityIndicator color={theme.colors.primary} /></View>;

  const buildReceiptText = () => {
    return `RECIBO Nº ${r.receipt_number}

Recebi de ${r.payer?.name || ''}, inscrito(a) no CPF/CNPJ ${r.payer?.cpf_cnpj || ''}, a importância de ${formatBRL(r.value)} (${numberToWords(r.value)}), referente a ${r.reference}.

Pagamento efetuado via ${r.payment_method}.

Para clareza e validade, firmo o presente recibo.

${formatDate(r.payment_date)}

_______________________________
${r.receiver?.name || ''}
CPF/CNPJ: ${r.receiver?.cpf_cnpj || ''}

${r.notes ? `Obs: ${r.notes}` : ''}`;
  };

  const share = async () => {
    try { await Share.share({ message: buildReceiptText(), title: `Recibo ${r.receipt_number}` }); }
    catch (e: any) { Alert.alert('Erro', e.message); }
  };

  return (
    <SafeAreaView style={s.safe}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Ionicons name="close" size={26} color={theme.colors.text} /></TouchableOpacity>
        <Text style={s.title}>Recibo</Text>
        <TouchableOpacity testID="share-receipt" onPress={share}><Ionicons name="share-outline" size={24} color={theme.colors.primary} /></TouchableOpacity>
      </View>
      <ScrollView contentContainerStyle={{ padding: 20 }}>
        <View style={s.docBox}>
          <View style={s.headerBox}>
            <View>
              <Text style={s.overline}>RECIBO</Text>
              <Text style={s.docNumber}>Nº {r.receipt_number}</Text>
            </View>
            <Text style={s.docValue}>{formatBRL(r.value)}</Text>
          </View>

          <View style={s.divider} />

          <Text style={s.declarText}>
            Recebi de <Text style={s.bold}>{r.payer?.name}</Text>, CPF/CNPJ <Text style={s.bold}>{r.payer?.cpf_cnpj}</Text>, a importância de <Text style={s.bold}>{formatBRL(r.value)}</Text> ({numberToWords(r.value)}), referente a <Text style={s.bold}>{r.reference}</Text>.
          </Text>

          <Text style={s.declarText}>Pagamento via <Text style={s.bold}>{r.payment_method}</Text> em <Text style={s.bold}>{formatDate(r.payment_date)}</Text>.</Text>

          {r.notes ? <Text style={[s.declarText, { fontStyle: 'italic', marginTop: 8 }]}>Obs: {r.notes}</Text> : null}

          <View style={s.divider} />

          <View style={s.gridBox}>
            <View style={s.gridItem}>
              <Text style={s.label}>PAGADOR</Text>
              <Text style={s.gridVal}>{r.payer?.name}</Text>
              <Text style={s.gridSub}>{r.payer?.cpf_cnpj}</Text>
            </View>
            <View style={s.gridItem}>
              <Text style={s.label}>RECEBEDOR</Text>
              <Text style={s.gridVal}>{r.receiver?.name}</Text>
              <Text style={s.gridSub}>{r.receiver?.cpf_cnpj}</Text>
            </View>
          </View>

          <View style={s.signLine} />
          <Text style={s.signName}>{r.receiver?.name}</Text>
          <Text style={s.signSub}>CPF/CNPJ: {r.receiver?.cpf_cnpj}</Text>
        </View>

        <TouchableOpacity testID="export-receipt" style={s.exportBtn} onPress={share}>
          <Ionicons name="share-outline" size={18} color="#fff" />
          <Text style={s.exportText}>COMPARTILHAR / EXPORTAR</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: theme.colors.bgSecondary },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 20, borderBottomWidth: 1, borderBottomColor: theme.colors.border, backgroundColor: theme.colors.bg },
  title: { fontSize: 18, fontWeight: '700', color: theme.colors.text },
  docBox: { backgroundColor: theme.colors.bg, padding: 24, borderRadius: 12, borderWidth: 1, borderColor: theme.colors.border },
  headerBox: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  overline: { fontSize: 10, color: theme.colors.textSecondary, letterSpacing: 2, fontWeight: '700' },
  docNumber: { fontSize: 14, fontWeight: '700', color: theme.colors.text, marginTop: 4 },
  docValue: { fontSize: 28, fontWeight: '800', color: theme.colors.primary, letterSpacing: -1 },
  divider: { height: 1, backgroundColor: theme.colors.border, marginVertical: 20 },
  declarText: { fontSize: 14, color: theme.colors.text, lineHeight: 22 },
  bold: { fontWeight: '700' },
  gridBox: { flexDirection: 'row', gap: 12, marginBottom: 24 },
  gridItem: { flex: 1, padding: 12, backgroundColor: theme.colors.bgSecondary, borderRadius: 6 },
  label: { fontSize: 9, color: theme.colors.textSecondary, letterSpacing: 1.5, fontWeight: '700', marginBottom: 4 },
  gridVal: { fontSize: 13, fontWeight: '700', color: theme.colors.text },
  gridSub: { fontSize: 11, color: theme.colors.textSecondary, marginTop: 2 },
  signLine: { height: 1, backgroundColor: theme.colors.text, marginTop: 40, marginHorizontal: 40 },
  signName: { textAlign: 'center', fontSize: 12, fontWeight: '700', color: theme.colors.text, marginTop: 8 },
  signSub: { textAlign: 'center', fontSize: 10, color: theme.colors.textSecondary },
  exportBtn: { flexDirection: 'row', backgroundColor: theme.colors.primary, padding: 16, borderRadius: 8, justifyContent: 'center', alignItems: 'center', marginTop: 24, gap: 8 },
  exportText: { color: '#fff', fontWeight: '700', letterSpacing: 1, fontSize: 13 },
});
