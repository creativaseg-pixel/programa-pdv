import { useEffect, useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, ActivityIndicator, Share, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api, formatBRL, formatDate } from '../src/api';
import { theme } from '../src/theme';

export default function ContractView() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const [c, setC] = useState<any>(null);

  useEffect(() => { api.get(`/contracts/${id}`).then(setC); }, [id]);

  if (!c) return <View style={[s.safe, { justifyContent: 'center' }]}><ActivityIndicator color={theme.colors.primary} /></View>;

  const isLoc = c.type === 'locacao';
  const monthly = isLoc ? c.value : 0;

  const buildContractText = () => {
    const today = new Date().toLocaleDateString('pt-BR');
    if (isLoc) {
      return `CONTRATO DE LOCAÇÃO RESIDENCIAL

LOCADOR: ${c.landlord?.name || ''}, ${c.landlord?.cpf_cnpj || ''}, residente em ${c.landlord?.address || ''}, telefone ${c.landlord?.phone || ''}.

LOCATÁRIO: ${c.tenant?.name || ''}, ${c.tenant?.cpf_cnpj || ''}, residente em ${c.tenant?.address || ''}, telefone ${c.tenant?.phone || ''}.

OBJETO: O LOCADOR cede ao LOCATÁRIO, em locação, o imóvel situado em ${c.property?.address || ''}, ${c.property?.city || ''}/${c.property?.state || ''}, conforme cadastrado.

CLÁUSULA 1ª - PRAZO: O prazo da locação é de ${formatDate(c.start_date)} a ${formatDate(c.end_date || '')}.

CLÁUSULA 2ª - VALOR: O aluguel mensal é de ${formatBRL(c.value)}, a ser pago até o dia ${c.payment_day} de cada mês.

CLÁUSULA 3ª - REAJUSTE: O valor será reajustado anualmente pelo índice ${c.index}.

CLÁUSULA 4ª - GARANTIA: ${c.deposit_value > 0 ? `Caução de ${formatBRL(c.deposit_value)}.` : 'Sem garantia.'}

CLÁUSULA 5ª - MULTA E JUROS: Em caso de atraso, incidirá multa de 10% sobre o valor devido, acrescida de juros de mora de 1% ao mês, conforme Lei 8.245/91 (Lei do Inquilinato).

CLÁUSULA 6ª - CONDIÇÕES: ${c.extra_terms || 'Demais condições conforme legislação vigente.'}

Local e data: _________________, ${today}.

_______________________________
LOCADOR

_______________________________
LOCATÁRIO

_______________________________
TESTEMUNHA 1

_______________________________
TESTEMUNHA 2`;
    }
    return `CONTRATO DE COMPRA E VENDA DE IMÓVEL

VENDEDOR: ${c.landlord?.name || ''}, ${c.landlord?.cpf_cnpj || ''}.
COMPRADOR: ${c.tenant?.name || ''}, ${c.tenant?.cpf_cnpj || ''}.

OBJETO: Imóvel situado em ${c.property?.address || ''}, ${c.property?.city || ''}/${c.property?.state || ''}.

VALOR DA TRANSAÇÃO: ${formatBRL(c.value)}.

COMISSÃO: ${c.commission_pct}% sobre o valor da transação = ${formatBRL(c.value * c.commission_pct / 100)}.

CONDIÇÕES: ${c.extra_terms || 'Conforme legislação vigente (Código Civil, Lei 6.766/79).'}

Data: ${today}

_______________________________
VENDEDOR

_______________________________
COMPRADOR`;
  };

  const share = async () => {
    try {
      await Share.share({ message: buildContractText(), title: `Contrato ${c.id.slice(0, 8)}` });
    } catch (e: any) { Alert.alert('Erro', e.message); }
  };

  return (
    <SafeAreaView style={s.safe}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Ionicons name="close" size={26} color={theme.colors.text} /></TouchableOpacity>
        <Text style={s.title}>Contrato</Text>
        <TouchableOpacity testID="share-contract" onPress={share}><Ionicons name="share-outline" size={24} color={theme.colors.primary} /></TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={{ padding: 20 }}>
        <View style={s.badge}>
          <Text style={s.badgeText}>{isLoc ? 'CONTRATO DE LOCAÇÃO' : 'COMPRA E VENDA'}</Text>
        </View>

        <Text style={s.docTitle}>{isLoc ? 'Contrato de Locação Residencial' : 'Contrato de Compra e Venda'}</Text>
        <Text style={s.docSub}>Conforme Lei 8.245/91 (Lei do Inquilinato) e Código Civil</Text>

        <Section title="PARTES">
          <Row label={isLoc ? 'Locador' : 'Vendedor'} value={c.landlord?.name || '-'} />
          <Row label="CPF/CNPJ" value={c.landlord?.cpf_cnpj || '-'} />
          <Row label={isLoc ? 'Locatário' : 'Comprador'} value={c.tenant?.name || '-'} />
          <Row label="CPF/CNPJ" value={c.tenant?.cpf_cnpj || '-'} />
        </Section>

        <Section title="IMÓVEL">
          <Row label="Endereço" value={c.property?.address || '-'} />
          <Row label="Cidade/UF" value={`${c.property?.city || ''}/${c.property?.state || ''}`} />
          <Row label="Tipo" value={c.property?.type || '-'} />
        </Section>

        <Section title="CONDIÇÕES FINANCEIRAS">
          <Row label={isLoc ? 'Aluguel mensal' : 'Valor total'} value={formatBRL(c.value)} highlight />
          {isLoc && <>
            <Row label="Dia de pagamento" value={`Todo dia ${c.payment_day}`} />
            <Row label="Reajuste" value={`Anual pelo ${c.index}`} />
            {c.deposit_value > 0 && <Row label="Caução" value={formatBRL(c.deposit_value)} />}
            <Row label="Multa por atraso" value="10% + 1% a.m. de juros" />
          </>}
          <Row label="Comissão" value={`${c.commission_pct}% = ${formatBRL(c.value * c.commission_pct / 100)}`} />
        </Section>

        <Section title="VIGÊNCIA">
          <Row label="Início" value={formatDate(c.start_date)} />
          <Row label="Término" value={formatDate(c.end_date || '') || 'Indeterminado'} />
        </Section>

        {c.extra_terms ? (
          <Section title="CLÁUSULAS ADICIONAIS">
            <Text style={s.terms}>{c.extra_terms}</Text>
          </Section>
        ) : null}

        <View style={s.signBox}>
          <View style={s.sign}><Text style={s.signLabel}>{isLoc ? 'LOCADOR' : 'VENDEDOR'}</Text></View>
          <View style={s.sign}><Text style={s.signLabel}>{isLoc ? 'LOCATÁRIO' : 'COMPRADOR'}</Text></View>
        </View>

        <TouchableOpacity testID="export-contract" style={s.exportBtn} onPress={share}>
          <Ionicons name="share-outline" size={18} color="#fff" />
          <Text style={s.exportText}>COMPARTILHAR / EXPORTAR</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

function Section({ title, children }: any) {
  return (
    <View style={s.section}>
      <Text style={s.sectionTitle}>{title}</Text>
      <View style={s.sectionBody}>{children}</View>
    </View>
  );
}

function Row({ label, value, highlight }: any) {
  return (
    <View style={s.row}>
      <Text style={s.rowLabel}>{label}</Text>
      <Text style={[s.rowValue, highlight && s.rowHighlight]}>{value}</Text>
    </View>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: theme.colors.bg },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 20, borderBottomWidth: 1, borderBottomColor: theme.colors.border },
  title: { fontSize: 18, fontWeight: '700', color: theme.colors.text },
  badge: { alignSelf: 'flex-start', backgroundColor: theme.colors.text, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 3, marginBottom: 12 },
  badgeText: { color: '#fff', fontSize: 10, fontWeight: '700', letterSpacing: 1.5 },
  docTitle: { fontSize: 24, fontWeight: '800', color: theme.colors.text, letterSpacing: -0.5 },
  docSub: { fontSize: 12, color: theme.colors.textSecondary, fontStyle: 'italic', marginTop: 6, marginBottom: 20 },
  section: { marginTop: 16 },
  sectionTitle: { fontSize: 10, color: theme.colors.textSecondary, letterSpacing: 2, fontWeight: '700', marginBottom: 8 },
  sectionBody: { padding: 16, backgroundColor: theme.colors.bgSecondary, borderRadius: 8, borderWidth: 1, borderColor: theme.colors.border },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8 },
  rowLabel: { fontSize: 13, color: theme.colors.textSecondary, flex: 1 },
  rowValue: { fontSize: 13, color: theme.colors.text, fontWeight: '600', textAlign: 'right', flex: 1 },
  rowHighlight: { fontSize: 18, fontWeight: '800', color: theme.colors.primary },
  terms: { fontSize: 13, color: theme.colors.text, lineHeight: 20 },
  signBox: { flexDirection: 'row', marginTop: 40, gap: 16 },
  sign: { flex: 1, borderTopWidth: 1, borderTopColor: theme.colors.text, paddingTop: 8, alignItems: 'center' },
  signLabel: { fontSize: 10, color: theme.colors.textSecondary, letterSpacing: 1.5, fontWeight: '700' },
  exportBtn: { flexDirection: 'row', backgroundColor: theme.colors.primary, padding: 16, borderRadius: 8, justifyContent: 'center', alignItems: 'center', marginTop: 32, gap: 8 },
  exportText: { color: '#fff', fontWeight: '700', letterSpacing: 1, fontSize: 13 },
});
